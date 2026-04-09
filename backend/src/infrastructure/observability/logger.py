"""Structured JSON logger — every agent emits events with trace_id."""
import json
import logging
import os
import sys
from datetime import datetime, timezone
from src.config import settings

# Ensure logs directory exists
os.makedirs("./logs", exist_ok=True)

_handlers = [logging.StreamHandler(sys.stdout)]
try:
    _file_handler = logging.FileHandler("./logs/agent.log", encoding="utf-8")
    _handlers.append(_file_handler)
except Exception:
    pass

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    handlers=_handlers,
    format="%(message)s",
)
logger = logging.getLogger("sre-agent")


def log_event(
    stage: str,
    status: str,
    trace_id: str,
    duration_ms: int,
    incident_id: int | None = None,
    metadata: dict | None = None,
) -> None:
    """Emit a structured JSON log event. Called by every agent on completion."""
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trace_id": trace_id,
        "stage": stage,
        "incident_id": incident_id,
        "status": status,
        "duration_ms": duration_ms,
        "metadata": metadata or {},
    }
    logger.info(json.dumps(payload))
