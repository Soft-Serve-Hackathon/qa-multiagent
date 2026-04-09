"""Observability event persistence — writes events to SQLite for the /api/observability/events endpoint."""
import json
import time
from contextlib import contextmanager
from src.infrastructure.observability.logger import log_event
from src.domain.entities import ObservabilityEvent
from src.infrastructure.database import SessionLocal


def emit_event(
    stage: str,
    status: str,
    trace_id: str,
    duration_ms: int,
    incident_id: int | None = None,
    metadata: dict | None = None,
) -> None:
    """Persist an observability event to SQLite and emit to log."""
    log_event(stage, status, trace_id, duration_ms, incident_id, metadata)
    db = SessionLocal()
    try:
        event = ObservabilityEvent(
            trace_id=trace_id,
            stage=stage,
            incident_id=incident_id,
            status=status,
            duration_ms=duration_ms,
            event_metadata=json.dumps(metadata or {}),
        )
        db.add(event)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


@contextmanager
def timed_stage(stage: str, trace_id: str, incident_id: int | None = None, metadata: dict | None = None):
    """Context manager that automatically times a stage and emits its event."""
    start = time.monotonic()
    try:
        yield
        duration_ms = int((time.monotonic() - start) * 1000)
        emit_event(stage, "success", trace_id, duration_ms, incident_id, metadata)
    except Exception as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        emit_event(stage, "error", trace_id, duration_ms, incident_id, {**(metadata or {}), "error": str(exc)})
        raise
