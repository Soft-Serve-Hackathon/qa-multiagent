"""Pydantic request/response schemas — strict contracts matching api-contracts.md."""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


# ── Responses ─────────────────────────────────────────────────────────────────
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
    trello_card_id: Optional[str] = None
    trello_card_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    uptime_seconds: int
    database: str = "connected"
    mock_mode: bool


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


class ErrorResponse(BaseModel):
    error: str
    message: str
    trace_id: Optional[str] = None
