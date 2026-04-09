"""Domain enums — incident status, severity, notification types."""
from enum import Enum


class IncidentStatus(str, Enum):
    RECEIVED = "received"
    TRIAGING = "triaging"
    DEDUPLICATED = "deduplicated"   # Linked to existing ticket, no new card created
    TICKETED = "ticketed"
    NOTIFIED = "notified"
    RESOLVED = "resolved"
    ERROR = "error"


class Severity(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class AttachmentType(str, Enum):
    IMAGE = "image"
    LOG = "log"


class NotificationType(str, Enum):
    TEAM_ALERT = "team_alert"
    REPORTER_CONFIRMATION = "reporter_confirmation"
    REPORTER_RESOLUTION = "reporter_resolution"


class NotificationChannel(str, Enum):
    SLACK = "slack"
    EMAIL = "email"


class NotificationStatus(str, Enum):
    SENT = "sent"
    FAILED = "failed"
    MOCKED = "mocked"


class TicketStatus(str, Enum):
    PENDING = "pending"
    CREATED = "created"
    FAILED = "failed"


class ObservabilityStage(str, Enum):
    INGEST = "ingest"
    TRIAGE = "triage"
    QA_SCOPE = "qa_scope"
    FIX_RECOMMENDATION = "fix_recommendation"
    TICKET = "ticket"
    NOTIFY = "notify"
    RESOLVED = "resolved"


class EventStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    DEDUPLICATED = "deduplicated"   # Ticket skipped — linked to existing
    SKIPPED = "skipped"
