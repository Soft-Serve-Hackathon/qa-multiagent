"""NotifyAgent — dispatches Slack alert and reporter email. Severity-based escalation."""
import time
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from src.domain.entities import Incident, Ticket, NotificationLog
from src.application.dto import TriageResultDTO, TicketDTO
from src.infrastructure.external.slack_client import SlackClient
from src.infrastructure.external.sendgrid_client import SendGridClient
from src.infrastructure.observability.events import emit_event
from src.config import settings


class NotifyAgent:
    """
    Responsibility: Send Slack alert to team and confirmation email to reporter.
    Persists NotificationLog entries. Does NOT generate content — receives it as DTOs.
    """

    def __init__(self, db: Session):
        self._db = db
        self._slack = SlackClient()
        self._email = SendGridClient()

    def process(
        self,
        triage: TriageResultDTO,
        ticket: TicketDTO,
        notification_type: str = "team_and_reporter",
    ) -> None:
        start = time.monotonic()
        incident: Incident = self._db.query(Incident).filter(Incident.id == triage.incident_id).first()
        notifications_sent = []

        # 1. Slack alert to team
        slack_ok = self._slack.post_incident_alert(
            title=incident.title,
            description=incident.description,
            severity=triage.severity,
            affected_module=triage.affected_module,
            confidence=triage.confidence_score,
            trello_url=ticket.trello_card_url,
            trace_id=triage.trace_id,
        )
        self._log_notification(
            incident_id=incident.id,
            channel="slack",
            recipient=settings.SLACK_CHANNEL,
            notification_type="team_alert",
            content_summary=f"[{triage.severity}] {incident.title}",
            status="sent" if slack_ok else "failed",
        )
        notifications_sent.append("slack")

        # 2. Confirmation email to reporter
        email_ok = self._email.send_confirmation(
            to_email=incident.reporter_email,
            incident_title=incident.title,
            severity=triage.severity,
            trello_card_id=ticket.trello_card_id,
            trello_card_url=ticket.trello_card_url,
        )
        self._log_notification(
            incident_id=incident.id,
            channel="email",
            recipient=incident.reporter_email,
            notification_type="reporter_confirmation",
            content_summary=f"Confirmation for: {incident.title}",
            status="sent" if email_ok else "failed",
        )
        notifications_sent.append("email")

        # 3. Update incident status
        incident.status = "notified"
        self._db.commit()

        duration_ms = int((time.monotonic() - start) * 1000)
        emit_event(
            "notify", "success", triage.trace_id, duration_ms,
            incident_id=incident.id,
            metadata={
                "channels": notifications_sent,
                "slack_ok": slack_ok,
                "email_ok": email_ok,
                "mock": settings.MOCK_INTEGRATIONS,
            },
        )

    def send_resolution(self, incident: Incident, ticket: Ticket) -> None:
        """Called by ResolutionWatcher when a card moves to Done."""
        start = time.monotonic()
        resolved_at = datetime.now(timezone.utc).isoformat()

        self._slack.post_resolution_notice(
            title=incident.title,
            trello_url=ticket.trello_card_url or "",
            trace_id=incident.trace_id,
        )
        self._email.send_resolution(
            to_email=incident.reporter_email,
            incident_title=incident.title,
            trello_card_id=ticket.trello_card_id or "",
            trello_card_url=ticket.trello_card_url or "",
            resolved_at=resolved_at,
        )
        self._log_notification(
            incident_id=incident.id,
            channel="email",
            recipient=incident.reporter_email,
            notification_type="reporter_resolution",
            content_summary=f"Resolution for: {incident.title}",
            status="sent",
        )
        incident.status = "resolved"
        self._db.commit()

        duration_ms = int((time.monotonic() - start) * 1000)
        emit_event(
            "resolved", "success", incident.trace_id, duration_ms,
            incident_id=incident.id,
            metadata={"resolved_at": resolved_at},
        )

    def _log_notification(
        self, incident_id: int, channel: str, recipient: str,
        notification_type: str, content_summary: str, status: str,
    ) -> None:
        log = NotificationLog(
            incident_id=incident_id,
            channel=channel,
            recipient=recipient,
            notification_type=notification_type,
            content_summary=content_summary,
            status=status,
        )
        self._db.add(log)
        self._db.commit()
