"""
API Request/Response Models.

Pydantic schemas for incident intake and API responses.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# POST /api/incidents — response
# ---------------------------------------------------------------------------

class IncidentCreatedResponse(BaseModel):
    incident_id: int
    trace_id: str
    status: str = "received"
    message: str = (
        "Your incident report has been received. "
        "Ticket creation is in progress. "
        "You will be notified by email."
    )


# ---------------------------------------------------------------------------
# GET /api/incidents/{trace_id} — response
# ---------------------------------------------------------------------------

class IncidentStatusResponse(BaseModel):
    incident_id: int
    trace_id: str
    title: str
    status: str
    created_at: datetime
    updated_at: datetime
    # Populated after triage completes
    severity: Optional[str] = None
    affected_module: Optional[str] = None
    triage_summary: Optional[str] = None
    suggested_files: Optional[list[str]] = None
    confidence_score: Optional[float] = None
    # Populated after ticket is created
    ticket_id: Optional[str] = None
    ticket_url: Optional[str] = None


# ---------------------------------------------------------------------------
# GET /api/observability/events — response
# ---------------------------------------------------------------------------

class ObservabilityEventResponse(BaseModel):
    id: int
    trace_id: str
    stage: str
    incident_id: Optional[int] = None
    status: str
    duration_ms: int
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ObservabilityEventsListResponse(BaseModel):
    events: list[ObservabilityEventResponse]
    total: int


# ---------------------------------------------------------------------------
# GET /api/dashboard/stats — response
# ---------------------------------------------------------------------------

class SeverityBreakdown(BaseModel):
    P1: int = 0
    P2: int = 0
    P3: int = 0
    P4: int = 0


class StatusBreakdown(BaseModel):
    received: int = 0
    triaging: int = 0
    deduplicated: int = 0
    ticketed: int = 0
    notified: int = 0
    resolved: int = 0


class ModuleCount(BaseModel):
    module: str
    count: int


class RecentIncident(BaseModel):
    incident_id: int
    trace_id: str
    title: str
    status: str
    severity: Optional[str] = None
    affected_module: Optional[str] = None
    confidence_score: Optional[float] = None
    ticket_id: Optional[str] = None
    ticket_url: Optional[str] = None
    deduplicated: bool = False
    created_at: datetime


class DashboardStatsResponse(BaseModel):
    total_incidents: int
    severity_breakdown: SeverityBreakdown
    status_breakdown: StatusBreakdown
    top_modules: list[ModuleCount]
    avg_triage_ms: Optional[float] = None
    avg_ticket_ms: Optional[float] = None
    deduplication_rate: float = 0.0          # 0.0–1.0
    recent_incidents: list[RecentIncident]
    pipeline_success_rate: float = 0.0       # 0.0–1.0


# ---------------------------------------------------------------------------
# Error responses
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    error: str
    message: Optional[str] = None
    trace_id: Optional[str] = None
