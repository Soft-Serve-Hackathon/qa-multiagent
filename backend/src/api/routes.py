"""FastAPI route definitions — all HTTP endpoints for the SRE Incident Agent."""
import json
import time
from typing import Optional
from fastapi import APIRouter, Depends, Form, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.api.models import (
    IncidentCreatedResponse,
    IncidentStatusResponse,
    HealthResponse,
    ObservabilityListResponse,
    ObservabilityEventOut,
    ErrorResponse,
    DashboardStatsResponse,
    SeverityBreakdown,
    StatusBreakdown,
    ModuleCount,
    RecentIncident,
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
        return JSONResponse(status_code=400, content={"error": "prompt_injection_detected", "message": "Your report contains content that cannot be processed."})
    except InvalidEmailError:
        return JSONResponse(status_code=400, content={"error": "invalid_email", "message": "Invalid email format."})
    except UnsupportedFileTypeError:
        return JSONResponse(status_code=400, content={"error": "unsupported_file_type", "message": "File type not allowed. Use PNG, JPG, TXT or LOG."})
    except FileTooLargeError:
        return JSONResponse(status_code=400, content={"error": "file_too_large", "message": f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit."})
    except EmptyOrCorruptAttachmentError:
        return JSONResponse(status_code=400, content={"error": "empty_or_corrupt_attachment", "message": "Uploaded file is empty or unreadable."})
    except Exception:
        return JSONResponse(status_code=500, content={"error": "internal_server_error", "message": "An unexpected error occurred."})


@router.get("/incidents/{incident_id}", response_model=IncidentStatusResponse)
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail={"error": "incident_not_found"})

    triage = db.query(TriageResult).filter(TriageResult.incident_id == incident_id).first()
    ticket = db.query(Ticket).filter(Ticket.incident_id == incident_id).first()

    suggested_files = json.loads(triage.suggested_files) if triage and triage.suggested_files else None

    return IncidentStatusResponse(
        incident_id=incident.id,
        trace_id=incident.trace_id,
        title=incident.title,
        status=incident.status,
        severity=triage.severity if triage else None,
        affected_module=triage.affected_module if triage else None,
        confidence_score=triage.confidence_score if triage else None,
        technical_summary=triage.technical_summary if triage else None,
        suggested_files=suggested_files,
        trello_card_id=ticket.trello_card_id if ticket else None,
        trello_card_url=ticket.trello_card_url if ticket else None,
        deduplicated=incident.status == "deduplicated",
        linked_ticket_id=incident.linked_ticket_id,
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


# ── Dashboard ──────────────────────────────────────────────────────────────────

@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Incident.id)).scalar() or 0

    # Severity breakdown (from triage_results)
    sev_rows = (
        db.query(TriageResult.severity, func.count(TriageResult.id))
        .group_by(TriageResult.severity)
        .all()
    )
    sev_map = {r[0]: r[1] for r in sev_rows}
    severity_breakdown = SeverityBreakdown(
        P1=sev_map.get("P1", 0),
        P2=sev_map.get("P2", 0),
        P3=sev_map.get("P3", 0),
        P4=sev_map.get("P4", 0),
    )

    # Status breakdown
    status_rows = (
        db.query(Incident.status, func.count(Incident.id))
        .group_by(Incident.status)
        .all()
    )
    status_map = {r[0]: r[1] for r in status_rows}
    status_breakdown = StatusBreakdown(
        received=status_map.get("received", 0),
        triaging=status_map.get("triaging", 0),
        deduplicated=status_map.get("deduplicated", 0),
        ticketed=status_map.get("ticketed", 0),
        notified=status_map.get("notified", 0),
        resolved=status_map.get("resolved", 0),
    )

    # Top affected modules
    module_rows = (
        db.query(TriageResult.affected_module, func.count(TriageResult.id))
        .group_by(TriageResult.affected_module)
        .order_by(func.count(TriageResult.id).desc())
        .limit(6)
        .all()
    )
    top_modules = [ModuleCount(module=r[0], count=r[1]) for r in module_rows]

    # Avg latency from observability events
    triage_events = (
        db.query(ObservabilityEvent.duration_ms)
        .filter(ObservabilityEvent.stage == "triage", ObservabilityEvent.status == "success")
        .all()
    )
    avg_triage_ms = (
        sum(e[0] for e in triage_events) / len(triage_events) if triage_events else None
    )

    ticket_events = (
        db.query(ObservabilityEvent.duration_ms)
        .filter(ObservabilityEvent.stage == "ticket", ObservabilityEvent.status == "success")
        .all()
    )
    avg_ticket_ms = (
        sum(e[0] for e in ticket_events) / len(ticket_events) if ticket_events else None
    )

    # Rates
    dedup_count = status_map.get("deduplicated", 0)
    deduplication_rate = round(dedup_count / total, 4) if total > 0 else 0.0

    success_count = status_map.get("notified", 0) + status_map.get("resolved", 0)
    pipeline_success_rate = round(success_count / total, 4) if total > 0 else 0.0

    # Recent incidents (last 20)
    recent_rows = (
        db.query(Incident)
        .order_by(Incident.created_at.desc())
        .limit(20)
        .all()
    )
    recent_incidents = []
    for inc in recent_rows:
        tr = db.query(TriageResult).filter(TriageResult.incident_id == inc.id).first()
        tk = db.query(Ticket).filter(Ticket.incident_id == inc.id).first()
        recent_incidents.append(RecentIncident(
            incident_id=inc.id,
            trace_id=inc.trace_id,
            title=inc.title,
            status=inc.status,
            severity=tr.severity if tr else None,
            affected_module=tr.affected_module if tr else None,
            confidence_score=tr.confidence_score if tr else None,
            trello_card_id=tk.trello_card_id if tk else None,
            trello_card_url=tk.trello_card_url if tk else None,
            deduplicated=inc.status == "deduplicated",
            created_at=inc.created_at.isoformat(),
        ))

    return DashboardStatsResponse(
        total_incidents=total,
        severity_breakdown=severity_breakdown,
        status_breakdown=status_breakdown,
        top_modules=top_modules,
        avg_triage_ms=avg_triage_ms,
        avg_ticket_ms=avg_ticket_ms,
        deduplication_rate=deduplication_rate,
        pipeline_success_rate=pipeline_success_rate,
        recent_incidents=recent_incidents,
    )


# ── Webhooks ───────────────────────────────────────────────────────────────────

@router.post("/webhooks/trello")
async def trello_webhook(payload: dict):
    """Receive Trello webhook events. Currently a no-op stub (polling used in MVP)."""
    return {"received": True}
