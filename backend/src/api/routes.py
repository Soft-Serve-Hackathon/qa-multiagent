"""
API Routes.

Endpoints for incident intake, status checks, and observability events.
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import desc

from ..agents.ingest_agent import IngestAgent
from .models import (
    ErrorResponse,
    IncidentCreatedResponse,
    IncidentStatusResponse,
    ObservabilityEventResponse,
    ObservabilityEventsListResponse,
)
from ..infrastructure.database import (
    IncidentModel,
    ObservabilityEventModel,
    TicketModel,
    TriageResultModel,
    get_db,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


# ---------------------------------------------------------------------------
# Pipeline runner — called as BackgroundTask after IngestAgent completes
# ---------------------------------------------------------------------------

def run_pipeline(incident_id: int, trace_id: str) -> None:
    """
    Runs the full agent pipeline in background.
    Each agent is imported inline to avoid circular imports at startup.
    If any agent fails, the error is captured in observability — the pipeline stops.
    """
    try:
        from ..agents.triage_agent import TriageAgent
        TriageAgent().process(incident_id, trace_id)
    except Exception as exc:
        logger.error(f"[{trace_id}] TriageAgent failed: {exc}")
        return

    try:
        from ..agents.ticket_agent import TicketAgent
        TicketAgent().process(incident_id, trace_id)
    except Exception as exc:
        logger.error(f"[{trace_id}] TicketAgent failed: {exc}")
        return

    try:
        from ..agents.notify_agent import NotifyAgent
        NotifyAgent().process(incident_id, trace_id)
    except Exception as exc:
        logger.error(f"[{trace_id}] NotifyAgent failed: {exc}")


# ---------------------------------------------------------------------------
# POST /api/incidents
# ---------------------------------------------------------------------------

@router.post("/incidents", status_code=201, response_model=IncidentCreatedResponse)
async def create_incident(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    description: str = Form(...),
    reporter_email: str = Form(...),
    attachment: Optional[UploadFile] = File(None),
):
    """
    Receive an incident report, validate it, persist it, and kick off the
    triage pipeline asynchronously. Returns HTTP 201 immediately.
    """
    agent = IngestAgent()
    incident_id, trace_id = await agent.process(
        title=title,
        description=description,
        reporter_email=reporter_email,
        attachment=attachment,
    )

    background_tasks.add_task(run_pipeline, incident_id, trace_id)

    return IncidentCreatedResponse(incident_id=incident_id, trace_id=trace_id)


# ---------------------------------------------------------------------------
# GET /api/incidents/{trace_id}
# ---------------------------------------------------------------------------

@router.get("/incidents/{trace_id}", response_model=IncidentStatusResponse)
def get_incident(trace_id: str):
    """
    Return current status of an incident, including triage result and ticket
    info once each pipeline stage completes.
    """
    with get_db() as db:
        incident: Optional[IncidentModel] = (
            db.query(IncidentModel)
            .filter(IncidentModel.trace_id == trace_id)
            .first()
        )

        if not incident:
            raise HTTPException(status_code=404, detail={"error": "incident_not_found"})

        # Extract incident data while session is open
        incident_id = incident.id
        incident_trace_id = incident.trace_id
        incident_title = incident.title
        incident_status = incident.status
        incident_created_at = incident.created_at
        incident_updated_at = incident.updated_at

        response = IncidentStatusResponse(
            incident_id=incident_id,
            trace_id=incident_trace_id,
            title=incident_title,
            status=incident_status,
            created_at=incident_created_at,
            updated_at=incident_updated_at,
        )

        # Enrich with triage data if available
        triage: Optional[TriageResultModel] = (
            db.query(TriageResultModel)
            .filter(TriageResultModel.incident_id == incident_id)
            .first()
        )
        if triage:
            response.severity = triage.severity
            response.affected_module = triage.affected_module
            response.triage_summary = triage.technical_summary
            response.suggested_files = triage.get_suggested_files()
            response.confidence_score = triage.confidence_score

        # Enrich with ticket data if available
        ticket: Optional[TicketModel] = (
            db.query(TicketModel)
            .filter(TicketModel.incident_id == incident_id)
            .first()
        )
        if ticket:
            response.ticket_id = ticket.trello_card_id
            response.ticket_url = ticket.trello_card_url

    return response


# ---------------------------------------------------------------------------
# GET /api/observability/events
# ---------------------------------------------------------------------------

@router.get("/observability/events", response_model=ObservabilityEventsListResponse)
def get_observability_events(
    trace_id: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """
    Return pipeline observability events. Useful for demo and debugging.
    Filter by trace_id or stage; defaults to latest 50 events.
    """
    with get_db() as db:
        query = db.query(ObservabilityEventModel)

        if trace_id:
            query = query.filter(ObservabilityEventModel.trace_id == trace_id)
        if stage:
            query = query.filter(ObservabilityEventModel.stage == stage)

        total = query.count()
        records = (
            query
            .order_by(desc(ObservabilityEventModel.created_at))
            .limit(limit)
            .all()
        )

    events = [
        ObservabilityEventResponse(
            id=r.id,
            trace_id=r.trace_id,
            stage=r.stage,
            incident_id=r.incident_id,
            status=r.status,
            duration_ms=r.duration_ms,
            metadata=r.get_metadata(),
            created_at=r.created_at,
        )
        for r in records
    ]

    return ObservabilityEventsListResponse(events=events, total=total)
