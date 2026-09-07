import asyncio
import json
import logging
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .demo import DemoProvider
from .providers import LiveProvider
from .schemas import Brief
from .workflow import run_workflow

ROOT = Path(__file__).resolve().parent.parent
logger = logging.getLogger("sceneready")
slots = asyncio.Semaphore(2)
document_slots = asyncio.Semaphore(1)
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
    try:
        async with asyncio.timeout(90):
            text, truncated = await LiveProvider().extract_pdf(document)
        return {"text": text, "characters": len(text), "truncated": truncated}
    except Exception as error:
        status = getattr(error, "status_code", getattr(error, "code", None))
        status = status if isinstance(status, int) else None
        logger.warning("document_extraction_failed error_type=%s http_status=%s", type(error).__name__, status)
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

    async def stream():
        try:
            async with asyncio.timeout(420):
                provider = DemoProvider() if demo else LiveProvider()
                async for event in run_workflow(brief, provider, demo=demo):
                    if await request.is_disconnected():
                        break
                    yield json.dumps(event, ensure_ascii=False) + "\n"
        except Exception as error:
            # Do not log uploaded scripts, retrieved text, credentials, or provider error bodies.
            status = getattr(error, "status_code", getattr(error, "code", None))
            status = status if isinstance(status, int) else None
            logger.warning("workflow_failed error_type=%s http_status=%s", type(error).__name__, status)
            detail = f"{type(error).__name__}" + (f", HTTP {status}" if status else "")
            yield json.dumps({"type": "error", "message": f"Run stopped ({detail}). No completed report was created. Check server configuration or try again."}) + "\n"
        finally:
            slots.release()
    return StreamingResponse(stream(), media_type="application/x-ndjson", headers={"X-Accel-Buffering": "no"})


app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
