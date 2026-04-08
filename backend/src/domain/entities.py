"""
Domain Entities.

Core aggregate roots: Incident, TriageResult, Ticket, NotificationLog.
These are pure Python dataclasses — no ORM dependencies.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .enums import (
    AffectedModule,
    AttachmentType,
    IncidentStatus,
    NotificationChannel,
    NotificationStatus,
    NotificationType,
    Severity,
    TicketStatus,
)


@dataclass
class Incident:
    title: str
    description: str
    reporter_email: str
    id: Optional[int] = None
    trace_id: Optional[str] = None
    attachment_type: Optional[AttachmentType] = None
    attachment_path: Optional[str] = None
    status: IncidentStatus = IncidentStatus.RECEIVED
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TriageResult:
    incident_id: int
    severity: Severity
    affected_module: AffectedModule
    technical_summary: str
    suggested_files: list[str]
    confidence_score: float
    id: Optional[int] = None
    raw_llm_response: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Ticket:
    incident_id: int
    trello_list_id: str
    id: Optional[int] = None
    trello_card_id: Optional[str] = None
    trello_card_url: Optional[str] = None
    status: TicketStatus = TicketStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None


@dataclass
class NotificationLog:
    incident_id: int
    channel: NotificationChannel
    recipient: str
    notification_type: NotificationType
    content_summary: str
    status: NotificationStatus
    id: Optional[int] = None
    sent_at: datetime = field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None
