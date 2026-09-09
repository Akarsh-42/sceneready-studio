import asyncio
import json
import os
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .demo import DemoProvider
from .observability import log_event
from .providers import LiveProvider
from .schemas import Brief
from .workflow import run_workflow
from .storyboard import StoryboardRequest, StoryboardProvider, generate_storyboard

ROOT = Path(__file__).resolve().parent.parent
slots = asyncio.Semaphore(2)
document_slots = asyncio.Semaphore(1)
storyboard_slots = asyncio.Semaphore(1)
BRIEF_BODY_LIMIT = 65_536
PDF_BODY_LIMIT = 8 * 1024 * 1024


@asynccontextmanager
async def lifespan(app):
    # Public Cloud Run endpoints must not expose an unprotected paid API.
    if os.environ.get("K_SERVICE") and len(os.environ.get("STUDIO_ACCESS_TOKEN", "")) < 24:
        raise RuntimeError("Set STUDIO_ACCESS_TOKEN to a private access code of at least 24 characters.")
    yield


app = FastAPI(title="SceneReady Studio", docs_url=None, redoc_url=None, lifespan=lifespan)


@app.middleware("http")
async def security(request: Request, call_next):
    body_limits = {
        "/api/storyboard": (BRIEF_BODY_LIMIT, "Scene is too large."),
        "/api/run": (BRIEF_BODY_LIMIT, "Brief is too large."),
        "/api/extract-document": (PDF_BODY_LIMIT, "PDF is too large. Use a file under 8 MiB."),
    }
    if request.url.path in body_limits:
        expected = os.environ.get("STUDIO_ACCESS_TOKEN", "")
        supplied = request.headers.get("Authorization", "").removeprefix("Bearer ")
        if expected and not secrets.compare_digest(supplied.encode(), expected.encode()):
            return JSONResponse({"detail": "Enter the studio access code."}, status_code=401)
        body_limit, body_error = body_limits[request.url.path]
        chunks, size = [], 0
        async for chunk in request.stream():
            size += len(chunk)
            if size > body_limit:
                return JSONResponse({"detail": body_error}, status_code=413)
            chunks.append(chunk)
        request._body = b"".join(chunks)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    )
    return response


@app.get("/")
async def index():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/api/config")
async def config():
    demo = os.environ.get("SCENEREADY_DEMO") == "1"
    return {"demo": demo, "access_required": bool(os.environ.get("STUDIO_ACCESS_TOKEN")),
            "configured": demo or bool(os.environ.get("GOOGLE_CLOUD_PROJECT") and os.environ.get("PARALLEL_API_KEY"))}


@app.get("/healthz")
async def health():
    return {"status": "ok"}


@app.post("/api/extract-document")
async def extract_document(request: Request):
    """Extract a bounded, reviewable brief from a screenplay PDF with Gemini."""
    media_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if media_type != "application/pdf":
        raise HTTPException(415, "Choose a PDF file.")
    document = await request.body()
    if not document.startswith(b"%PDF-"):
        raise HTTPException(400, "The selected file is not a valid PDF.")
    if os.environ.get("SCENEREADY_DEMO") == "1":
        raise HTTPException(503, "PDF extraction requires the live Gemini configuration.")
    if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
        raise HTTPException(503, "Google Cloud configuration is missing.")
    try:
        await asyncio.wait_for(document_slots.acquire(), timeout=0.1)
    except TimeoutError:
        raise HTTPException(429, "A PDF is already being processed. Please try again shortly.")
    operation_id, started = uuid4().hex[:12], time.monotonic()
    log_event("document_extraction_started", operation_id=operation_id, bytes=len(document))
    try:
        async with asyncio.timeout(90):
            text, truncated = await LiveProvider().extract_pdf(document)
        log_event(
            "document_extraction_completed",
            operation_id=operation_id,
            seconds=round(time.monotonic() - started, 3),
            bytes=len(document),
            truncated=truncated,
        )
        return {"text": text, "characters": len(text), "truncated": truncated}
    except Exception as error:
        status = getattr(error, "status_code", getattr(error, "code", None))
        status = status if isinstance(status, int) else None
        log_event(
            "document_extraction_failed",
            severity="warning",
            operation_id=operation_id,
            seconds=round(time.monotonic() - started, 3),
            error_type=type(error).__name__,
            http_status=status,
        )
        raise HTTPException(502, "Gemini could not extract this PDF. Try a smaller or clearer screenplay PDF.")
    finally:
        document_slots.release()


@app.post("/api/run")
async def run(brief: Brief, request: Request):
    demo = os.environ.get("SCENEREADY_DEMO") == "1"
    if not demo and not (os.environ.get("GOOGLE_CLOUD_PROJECT") and os.environ.get("PARALLEL_API_KEY")):
        raise HTTPException(503, "Live configuration is missing. Start with scripts/run_local.py.")
    try:
        await asyncio.wait_for(slots.acquire(), timeout=0.1)
    except TimeoutError:
        raise HTTPException(429, "Two runs are already active. Please try again shortly.")

    run_id = uuid4().hex[:12]

    async def stream():
        try:
            async with asyncio.timeout(420):
                provider = DemoProvider() if demo else LiveProvider()
                async for event in run_workflow(brief, provider, demo=demo, run_id=run_id):
                    if await request.is_disconnected():
                        log_event("run_disconnected", severity="warning", run_id=run_id)
                        break
                    yield json.dumps(event, ensure_ascii=False) + "\n"
        except Exception as error:
            # The field allowlist keeps scripts, excerpts, credentials, queries,
            # and provider error bodies out of logs.
            status = getattr(error, "status_code", getattr(error, "code", None))
            status = status if isinstance(status, int) else None
            log_event(
                "run_failed",
                severity="warning",
                run_id=run_id,
                error_type=type(error).__name__,
                http_status=status,
            )
            detail = f"{type(error).__name__}" + (f", HTTP {status}" if status else "")
            yield json.dumps({"type": "error", "message": f"Run stopped ({detail}). No completed report was created. Check server configuration or try again."}) + "\n"
        finally:
            slots.release()
    return StreamingResponse(stream(), media_type="application/x-ndjson", headers={"X-Accel-Buffering": "no"})


@app.post("/api/storyboard")
async def storyboard(payload: StoryboardRequest, request: Request):
    if os.environ.get("SCENEREADY_DEMO") == "1":
        raise HTTPException(503, "Storyboards require a live scene and Google configuration.")
    if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
        raise HTTPException(503, "Google Cloud configuration is missing.")
    if not payload.scene.script_excerpt.strip():
        raise HTTPException(422, "This scene has no verified script excerpt. Run the breakdown again.")
    try:
        await asyncio.wait_for(storyboard_slots.acquire(), timeout=0.1)
    except TimeoutError:
        raise HTTPException(429, "A storyboard is already being generated. Try again shortly.")

    operation_id, started = uuid4().hex[:12], time.monotonic()
    log_event("storyboard_started", operation_id=operation_id, total_frames=payload.shot_count)

    async def stream():
        try:
            async with asyncio.timeout(380):
                async for event in generate_storyboard(payload, StoryboardProvider()):
                    if await request.is_disconnected():
                        log_event("storyboard_disconnected", severity="warning", operation_id=operation_id)
                        break
                    if event.get("type") == "complete":
                        log_event(
                            "storyboard_completed",
                            operation_id=operation_id,
                            seconds=round(time.monotonic() - started, 3),
                            successful_frames=event.get("successful"),
                            total_frames=event.get("total"),
                        )
                    yield json.dumps(event) + "\n"
        except Exception as error:
            log_event(
                "storyboard_failed",
                severity="warning",
                operation_id=operation_id,
                seconds=round(time.monotonic() - started, 3),
                error_type=type(error).__name__,
            )
            yield json.dumps({"type": "error", "message": "Storyboard stopped. Check Google model access or try again. Completed frames remain available."}) + "\n"
        finally:
            storyboard_slots.release()
    return StreamingResponse(stream(), media_type="application/x-ndjson")


app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
