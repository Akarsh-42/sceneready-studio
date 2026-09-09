"""Privacy-safe, machine-readable application events for Cloud Run logs."""
import json
import logging

logger = logging.getLogger("sceneready.events")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False

# Keep this allowlist small so accidental fields cannot expose screenplays,
# retrieved excerpts, access codes, provider bodies, or search queries.
_ALLOWED_FIELDS = {
    "run_id", "operation_id", "stage", "topic", "mode", "status", "seconds",
    "http_status", "error_type", "bytes", "truncated", "scene_count",
    "source_count", "task_count", "warning_count", "search_count",
    "successful_frames", "total_frames",
}


def log_event(event: str, *, severity: str = "info", **fields) -> None:
    """Write compact JSON containing only explicitly approved metadata fields."""
    payload = {"event": event}
    for key, value in fields.items():
        if key in _ALLOWED_FIELDS and value is not None and isinstance(value, (str, int, float, bool)):
            payload[key] = value
    message = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    level = severity if severity in {"debug", "info", "warning", "error", "critical"} else "info"
    getattr(logger, level)(message)
