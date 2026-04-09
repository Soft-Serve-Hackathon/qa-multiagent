"""FastAPI route definitions — all HTTP endpoints for the SRE Incident Agent."""
import json
import time
from typing import Optional
from fastapi import APIRouter, Depends, Form, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.api.models import (
    IncidentCreatedResponse,
    IncidentStatusResponse,
    HealthResponse,
    ObservabilityListResponse,
    ObservabilityEventOut,
    ErrorResponse,
)
from src.infrastructure.database import get_db
from src.domain.entities import Incident, TriageResult, Ticket, ObservabilityEvent
from src.domain.exceptions import (
    PromptInjectionDetected, InvalidEmailError,
    UnsupportedFileTypeError, FileTooLargeError, EmptyOrCorruptAttachmentError,
)
from src.config import settings

router = APIRouter()
_start_time = time.monotonic()


# ── Health ────────────────────────────────────────────────────────────────────
@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "error"
    return HealthResponse(
        version=settings.APP_VERSION,
        uptime_seconds=int(time.monotonic() - _start_time),
        database=db_status,
        mock_mode=settings.MOCK_INTEGRATIONS,
    )


# ── Incidents ─────────────────────────────────────────────────────────────────
@router.post("/incidents", response_model=IncidentCreatedResponse, status_code=201)
async def create_incident(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    description: str = Form(...),
    reporter_email: str = Form(...),
    attachment: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    from src.application.create_incident_use_case import CreateIncidentUseCase

    use_case = CreateIncidentUseCase(db)
    try:
        result = await use_case.execute(
            title=title,
            description=description,
            reporter_email=reporter_email,
            attachment=attachment,
            background_tasks=background_tasks,
        )
        return result
    except PromptInjectionDetected:
        return JSONResponse(
            status_code=400,
            content={"error": "prompt_injection_detected",
                     "message": "Your report contains content that cannot be processed. Please rephrase and try again."},
        )
    except InvalidEmailError:
        return JSONResponse(status_code=400, content={"error": "invalid_email", "message": "Invalid email format."})
    except UnsupportedFileTypeError:
        return JSONResponse(status_code=400, content={"error": "unsupported_file_type", "message": "File type not allowed. Use PNG, JPG, TXT or LOG."})
    except FileTooLargeError:
        return JSONResponse(status_code=400, content={"error": "file_too_large", "message": f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit."})
    except EmptyOrCorruptAttachmentError:
        return JSONResponse(status_code=400, content={"error": "empty_or_corrupt_attachment", "message": "Uploaded file is empty or unreadable."})
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"error": "internal_server_error", "message": "An unexpected error occurred. Please try again."},
        )


@router.get("/incidents/{incident_id}", response_model=IncidentStatusResponse)
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail={"error": "incident_not_found"})

    # Fetch related data
    triage = db.query(TriageResult).filter(TriageResult.incident_id == incident_id).first()
    ticket = db.query(Ticket).filter(Ticket.incident_id == incident_id).first()

    return IncidentStatusResponse(
        incident_id=incident.id,
        trace_id=incident.trace_id,
        title=incident.title,
        status=incident.status,
        severity=triage.severity if triage else None,
        affected_module=triage.affected_module if triage else None,
        trello_card_id=ticket.trello_card_id if ticket else None,
        trello_card_url=ticket.trello_card_url if ticket else None,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
    )


# ── Observability ──────────────────────────────────────────────────────────────
@router.get("/observability/events", response_model=ObservabilityListResponse)
def get_observability_events(
    trace_id: Optional[str] = None,
    stage: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(ObservabilityEvent)
    if trace_id:
        query = query.filter(ObservabilityEvent.trace_id == trace_id)
    if stage:
        query = query.filter(ObservabilityEvent.stage == stage)
    query = query.order_by(ObservabilityEvent.created_at.asc())
    total = query.count()
    events = query.limit(limit).all()

    return ObservabilityListResponse(
        events=[
            ObservabilityEventOut(
                id=e.id,
                trace_id=e.trace_id,
                stage=e.stage,
                incident_id=e.incident_id,
                status=e.status,
                duration_ms=e.duration_ms,
                metadata=json.loads(e.event_metadata) if e.event_metadata else {},
                created_at=e.created_at,
            )
            for e in events
        ],
        total=total,
    )


# ── Trello webhook (future) ───────────────────────────────────────────────────
@router.post("/webhooks/trello")
async def trello_webhook(payload: dict):
    """Receive Trello webhook events. Currently a no-op stub (polling used in MVP)."""
    return {"received": True}
