"""
Observability — Event Emitter.

Central function used by every agent to emit structured JSON events.
Contract: every event has trace_id, stage, status, duration_ms, metadata.
The trace_id flows unchanged from IngestAgent to ResolutionWatcher.
"""

import json
import logging
import time
from contextlib import contextmanager
from typing import Any, Generator, Optional

from ...domain.enums import ObservabilityStage, ObservabilityStatus

logger = logging.getLogger(__name__)


def emit_event(
    *,
    trace_id: str,
    stage: ObservabilityStage,
    status: ObservabilityStatus,
    duration_ms: int,
    incident_id: Optional[int] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Persist an observability event to the database and log it as structured JSON.

    Always call this — even on error paths — so the pipeline is fully traceable.
    Never include reporter_email in metadata.

    Returns the event dict (useful for testing / chaining).
    """
    from ...infrastructure.database import ObservabilityEventModel, get_db

    meta = metadata or {}
    event_dict = {
        "trace_id": trace_id,
        "stage": stage.value,
        "incident_id": incident_id,
        "status": status.value,
        "duration_ms": duration_ms,
        "metadata": meta,
    }

    # Structured log — always emitted regardless of DB success
    logger.info(json.dumps(event_dict))

    # Persist to DB
    try:
        with get_db() as db:
            record = ObservabilityEventModel(
                trace_id=trace_id,
                stage=stage.value,
                incident_id=incident_id,
                status=status.value,
                duration_ms=duration_ms,
                event_metadata=json.dumps(meta),
            )
            db.add(record)
    except Exception as exc:
        # Never let observability failures crash the pipeline
        logger.error(
            json.dumps({
                "observability_error": str(exc),
                "trace_id": trace_id,
                "stage": stage.value,
            })
        )

    return event_dict


@contextmanager
def timed_stage(
    trace_id: str,
    stage: ObservabilityStage,
    incident_id: Optional[int] = None,
    extra_metadata: Optional[dict[str, Any]] = None,
) -> Generator[dict[str, Any], None, None]:
    """
    Context manager that automatically emits a success or error event
    with the elapsed duration.

    Usage:
        with timed_stage(trace_id, ObservabilityStage.INGEST, incident_id=42) as meta:
            meta["attachment_type"] = "image"
            # ... do work ...
    """
    meta: dict[str, Any] = extra_metadata.copy() if extra_metadata else {}
    start = time.monotonic()
    try:
        yield meta
        duration_ms = int((time.monotonic() - start) * 1000)
        emit_event(
            trace_id=trace_id,
            stage=stage,
            status=ObservabilityStatus.SUCCESS,
            duration_ms=duration_ms,
            incident_id=incident_id,
            metadata=meta,
        )
    except Exception as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        meta["error"] = str(exc)
        emit_event(
            trace_id=trace_id,
            stage=stage,
            status=ObservabilityStatus.ERROR,
            duration_ms=duration_ms,
            incident_id=incident_id,
            metadata=meta,
        )
        raise
