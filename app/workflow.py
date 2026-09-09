"""Fixed-order workflow: extract -> research -> assess -> validate -> review."""
import asyncio
import time
from datetime import datetime, timezone
from uuid import uuid4

from .observability import log_event
from .prompts import PROMPT_VERSION
from .schemas import normalized, validate_report

TOPICS = {
    "location_access": "film shooting permission official location authority",
    "night_filming": "night film shooting permission official guidance",
    "drone": "drone filming official aviation guidance",
    "road_control": "filming road closure traffic control official guidance",
    "stunts": "film stunt safety official guidance",
    "animals": "animals film shooting official guidance",
    "minors": "child performers filming official guidance",
}


async def run_workflow(brief, provider, demo=False, run_id=None):
    run_id, started = run_id or uuid4().hex[:12], time.monotonic()
    mode = "offline_rehearsal" if demo else "live"
    warnings, trace = [], []
    log_event("run_started", run_id=run_id, mode=mode)
    if demo:
        warnings.append("OFFLINE REHEARSAL: no Gemini or Parallel requests were made. Results are illustrative.")
    yield {"type": "stage", "stage": "breakdown", "status": "running"}
    stage_start = time.monotonic()
    breakdown = await asyncio.wait_for(provider.breakdown(brief), timeout=120)
    ids = [scene.id for scene in breakdown.scenes]
    if len(ids) != len(set(ids)):
        raise ValueError("The breakdown returned duplicate scene IDs. Try the run again.")
    for scene in breakdown.scenes:
        if not normalized(scene.script_excerpt) or normalized(scene.script_excerpt) not in normalized(brief.script):
            scene.script_excerpt = ""
            warnings.append(f"{scene.id}: an unmatched script excerpt was removed; review the extracted scene.")
    stage_seconds = round(time.monotonic() - stage_start, 2)
    trace.append({"stage": "breakdown", "seconds": stage_seconds})
    log_event("stage_completed", run_id=run_id, stage="breakdown", seconds=stage_seconds, scene_count=len(breakdown.scenes))
    yield {"type": "stage", "stage": "breakdown", "status": "complete", "breakdown": breakdown.model_dump()}

    yield {"type": "stage", "stage": "research", "status": "running"}
    stage_start = time.monotonic()
    # Guaranteed research stage; the model cannot skip it or increase its call budget.
    topics = list(dict.fromkeys(["location_access", *breakdown.research_topics]))[:3]
    sources, seen, searches = [], set(), []
    for topic in topics:
        query = f"{brief.city} {TOPICS[topic]}"
        try:
            found = await asyncio.wait_for(provider.search(query), timeout=65)
            status = "success" if found else "no_results"
            if not found:
                warnings.append(f"No evidence returned for {topic.replace('_', ' ')}.")
            for source in found:
                if source.url not in seen:
                    seen.add(source.url)
                    source.id = f"E{len(sources) + 1:02d}"
                    sources.append(source)
        except Exception as error:
            status = "failed"
            warnings.append(f"Research for {topic.replace('_', ' ')} failed ({type(error).__name__}); requirements remain unknown.")
        searches.append({"topic": topic, "query": query, "status": status})
        log_event("research_topic_completed", run_id=run_id, stage="research", topic=topic, status=status)
        yield {"type": "research", "completed": len(searches), "total": len(topics), "status": status}
    stage_seconds = round(time.monotonic() - stage_start, 2)
    trace.append({"stage": "research", "seconds": stage_seconds, "searches": searches})
    log_event("stage_completed", run_id=run_id, stage="research", seconds=stage_seconds, source_count=len(sources), search_count=len(searches))
    yield {"type": "stage", "stage": "research", "status": "complete", "source_count": len(sources)}

    yield {"type": "stage", "stage": "planning", "status": "running"}
    stage_start = time.monotonic()
    assessment = await asyncio.wait_for(provider.assess(brief, breakdown, sources, warnings), timeout=120)
    stage_seconds = round(time.monotonic() - stage_start, 2)
    trace.append({"stage": "planning", "seconds": stage_seconds})
    log_event("stage_completed", run_id=run_id, stage="planning", seconds=stage_seconds)
    yield {"type": "stage", "stage": "planning", "status": "complete"}

    yield {"type": "stage", "stage": "validation", "status": "running"}
    stage_start = time.monotonic()
    tasks, validation_warnings = validate_report(assessment, breakdown, sources)
    warnings.extend(validation_warnings)
    stage_seconds = round(time.monotonic() - stage_start, 3)
    trace.append({"stage": "validation", "seconds": stage_seconds})
    log_event("stage_completed", run_id=run_id, stage="validation", seconds=stage_seconds)
    yield {"type": "stage", "stage": "validation", "status": "complete"}
    elapsed_seconds = round(time.monotonic() - started, 2)
    report = {
        "schema_version": "2.0", "run_id": run_id, "prompt_version": PROMPT_VERSION,
        "mode": mode,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": elapsed_seconds,
        "brief": brief.model_dump(mode="json"), "breakdown": breakdown.model_dump(),
        "sources": [source.model_dump() for source in sources], "tasks": tasks,
        "questions": assessment.questions, "warnings": warnings, "trace": trace,
        "notice": "Preliminary planning only. Matching an excerpt does not establish accuracy, currency, applicability, or permission to film.",
    }
    log_event(
        "run_completed", run_id=run_id, mode=mode, seconds=elapsed_seconds,
        scene_count=len(breakdown.scenes), source_count=len(sources),
        task_count=len(tasks), warning_count=len(warnings),
    )
    yield {"type": "result", "report": report}
