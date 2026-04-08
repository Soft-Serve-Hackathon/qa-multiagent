"""
Domain Enums.

Incident status, severity levels, impact categories, notification types, etc.
"""

from enum import Enum


class IncidentStatus(str, Enum):
    RECEIVED = "received"
    TRIAGING = "triaging"
    DEDUPLICATED = "deduplicated"  # Linked to existing ticket, no new card created
    TICKETED = "ticketed"
    NOTIFIED = "notified"
    RESOLVED = "resolved"


class Severity(str, Enum):
    P1 = "P1"  # System completely down — < 1 hour response
    P2 = "P2"  # Critical feature degraded — < 4 hours response
    P3 = "P3"  # Non-critical feature affected — < 24 hours response
    P4 = "P4"  # Minor bug / cosmetic — < 1 week response


class AffectedModule(str, Enum):
    CART = "cart"
    ORDER = "order"
    PAYMENT = "payment"
    INVENTORY = "inventory"
    PRODUCT = "product"
    CUSTOMER = "customer"
    SHIPPING = "shipping"
    DISCOUNT = "discount"
    UNKNOWN = "unknown"


class AttachmentType(str, Enum):
    IMAGE = "image"
    LOG = "log"


class TicketStatus(str, Enum):
    PENDING = "pending"
    CREATED = "created"
    FAILED = "failed"


class NotificationChannel(str, Enum):
    SLACK = "slack"
    EMAIL = "email"


class NotificationType(str, Enum):
    TEAM_ALERT = "team_alert"
    REPORTER_CONFIRMATION = "reporter_confirmation"
    REPORTER_RESOLUTION = "reporter_resolution"


class NotificationStatus(str, Enum):
    SENT = "sent"
    FAILED = "failed"
    MOCKED = "mocked"


class ObservabilityStage(str, Enum):
    INGEST = "ingest"
    TRIAGE = "triage"
    TICKET = "ticket"
    NOTIFY = "notify"
    RESOLVED = "resolved"


class ObservabilityStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    DEDUPLICATED = "deduplicated"  # Ticket skipped — linked to existing
