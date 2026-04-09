"""Pydantic request/response schemas — strict contracts matching api-contracts.md."""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


# ── Incident responses ────────────────────────────────────────────────────────

class IncidentCreatedResponse(BaseModel):
    incident_id: int
    trace_id: str
    status: str = "received"
    message: str = (
        "Your incident report has been received. "
        "Ticket creation is in progress. You will be notified by email."
    )


class IncidentStatusResponse(BaseModel):
    incident_id: int
    trace_id: str
    title: str
    status: str
    severity: Optional[str] = None
    affected_module: Optional[str] = None
    confidence_score: Optional[float] = None
    technical_summary: Optional[str] = None
    suggested_files: Optional[list] = None
    trello_card_id: Optional[str] = None
    trello_card_url: Optional[str] = None
    deduplicated: bool = False
    linked_ticket_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    uptime_seconds: int
    database: str = "connected"
    mock_mode: bool


# ── Observability ─────────────────────────────────────────────────────────────

class ObservabilityEventOut(BaseModel):
    id: int
    trace_id: str
    stage: str
    incident_id: Optional[int] = None
    status: str
    duration_ms: int
    metadata: dict
    created_at: datetime


class ObservabilityListResponse(BaseModel):
    events: list[ObservabilityEventOut]
    total: int


# ── Dashboard ─────────────────────────────────────────────────────────────────

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
    trello_card_id: Optional[str] = None
    trello_card_url: Optional[str] = None
    deduplicated: bool = False
    created_at: str


class DashboardStatsResponse(BaseModel):
    total_incidents: int
    severity_breakdown: SeverityBreakdown
    status_breakdown: StatusBreakdown
    top_modules: list[ModuleCount]
    avg_triage_ms: Optional[float] = None
    avg_ticket_ms: Optional[float] = None
    deduplication_rate: float = 0.0
    pipeline_success_rate: float = 0.0
    recent_incidents: list[RecentIncident]


# ── Errors ────────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    error: str
    message: str
    trace_id: Optional[str] = None
