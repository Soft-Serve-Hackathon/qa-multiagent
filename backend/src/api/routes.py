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
    DashboardStatsResponse,
    ErrorResponse,
    IncidentCreatedResponse,
    IncidentStatusResponse,
    ModuleCount,
    ObservabilityEventResponse,
    ObservabilityEventsListResponse,
    RecentIncident,
    SeverityBreakdown,
    StatusBreakdown,
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


# ---------------------------------------------------------------------------
# GET /api/dashboard/stats
# ---------------------------------------------------------------------------

@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats():
    """
    Aggregated statistics for the observability dashboard.
    Returns incident counts, severity/module breakdowns, latency averages,
    deduplication rate, and the 20 most recent incidents.
    """
    from collections import Counter, defaultdict

    with get_db() as db:
        # ── Total incidents ────────────────────────────────────────────────
        total = db.query(IncidentModel).count()

        # ── Status breakdown ───────────────────────────────────────────────
        status_rows = db.query(IncidentModel.status).all()
        status_counts: dict[str, int] = Counter(r.status for r in status_rows)

        # ── Severity breakdown (from triage results) ───────────────────────
        sev_rows = db.query(TriageResultModel.severity).all()
        sev_counts: dict[str, int] = Counter(r.severity for r in sev_rows)

        # ── Top modules ────────────────────────────────────────────────────
        mod_rows = db.query(TriageResultModel.affected_module).all()
        mod_counts: dict[str, int] = Counter(r.affected_module for r in mod_rows)
        top_modules = [
            ModuleCount(module=m, count=c)
            for m, c in sorted(mod_counts.items(), key=lambda x: -x[1])
        ][:6]

        # ── Avg latency from observability events ──────────────────────────
        triage_events = (
            db.query(ObservabilityEventModel.duration_ms)
            .filter(ObservabilityEventModel.stage == "triage")
            .filter(ObservabilityEventModel.status == "success")
            .all()
        )
        ticket_events = (
            db.query(ObservabilityEventModel.duration_ms)
            .filter(ObservabilityEventModel.stage == "ticket")
            .filter(ObservabilityEventModel.status == "success")
            .all()
        )
        avg_triage = (
            sum(r.duration_ms for r in triage_events) / len(triage_events)
            if triage_events else None
        )
        avg_ticket = (
            sum(r.duration_ms for r in ticket_events) / len(ticket_events)
            if ticket_events else None
        )

        # ── Deduplication rate ─────────────────────────────────────────────
        dedup_count = status_counts.get("deduplicated", 0)
        dedup_rate = (dedup_count / total) if total > 0 else 0.0

        # ── Pipeline success rate (reached notified or resolved) ───────────
        success_count = status_counts.get("notified", 0) + status_counts.get("resolved", 0)
        pipeline_success_rate = (success_count / total) if total > 0 else 0.0

        # ── Recent incidents (last 20) ─────────────────────────────────────
        recent_rows = (
            db.query(IncidentModel)
            .order_by(desc(IncidentModel.created_at))
            .limit(20)
            .all()
        )

        recent_incidents = []
        for inc in recent_rows:
            triage = (
                db.query(TriageResultModel)
                .filter(TriageResultModel.incident_id == inc.id)
                .first()
            )
            ticket = (
                db.query(TicketModel)
                .filter(TicketModel.incident_id == inc.id)
                .first()
            )
            recent_incidents.append(
                RecentIncident(
                    incident_id=inc.id,
                    trace_id=inc.trace_id,
                    title=inc.title,
                    status=inc.status,
                    severity=triage.severity if triage else None,
                    affected_module=triage.affected_module if triage else None,
                    confidence_score=triage.confidence_score if triage else None,
                    ticket_id=ticket.trello_card_id if ticket else None,
                    ticket_url=ticket.trello_card_url if ticket else None,
                    deduplicated=(inc.status == "deduplicated"),
                    created_at=inc.created_at,
                )
            )

    return DashboardStatsResponse(
        total_incidents=total,
        severity_breakdown=SeverityBreakdown(
            P1=sev_counts.get("P1", 0),
            P2=sev_counts.get("P2", 0),
            P3=sev_counts.get("P3", 0),
            P4=sev_counts.get("P4", 0),
        ),
        status_breakdown=StatusBreakdown(
            received=status_counts.get("received", 0),
            triaging=status_counts.get("triaging", 0),
            deduplicated=status_counts.get("deduplicated", 0),
            ticketed=status_counts.get("ticketed", 0),
            notified=status_counts.get("notified", 0),
            resolved=status_counts.get("resolved", 0),
        ),
        top_modules=top_modules,
        avg_triage_ms=avg_triage,
        avg_ticket_ms=avg_ticket,
        deduplication_rate=round(dedup_rate, 3),
        recent_incidents=recent_incidents,
        pipeline_success_rate=round(pipeline_success_rate, 3),
    )
