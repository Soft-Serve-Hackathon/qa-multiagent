"""
Notify Agent.

Sends notifications via Slack webhook and SendGrid email.
Notifies team in #incidents channel and reporter via email.
Persists notification logs and emits observability events.
Handles failures gracefully (partial success = partial notification).
"""

import json
import logging
import time
from datetime import datetime
from typing import Any, Optional

import httpx

from ..config import get_settings
from ..domain.enums import (
    IncidentStatus,
    NotificationChannel,
    NotificationType,
    NotificationStatus,
    ObservabilityStage,
    ObservabilityStatus,
)
from ..infrastructure.database import (
    IncidentModel,
    NotificationLogModel,
    TicketModel,
    TriageResultModel,
    get_db,
)
from ..infrastructure.observability.events import emit_event

logger = logging.getLogger(__name__)

# Email HTML template
EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #f5f5f5; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .header h1 {{ margin: 0 0 10px 0; color: #333; }}
        .severity {{ display: inline-block; padding: 4px 12px; border-radius: 4px; font-weight: bold; }}
        .severity-p1 {{ background-color: #ff4444; color: white; }}
        .severity-p2 {{ background-color: #ff9900; color: white; }}
        .severity-p3 {{ background-color: #ffcc00; color: #333; }}
        .severity-p4 {{ background-color: #44aa44; color: white; }}
        .section {{ margin: 20px 0; }}
        .section-title {{ font-weight: bold; font-size: 14px; color: #333; margin-bottom: 10px; }}
        .value {{ color: #666; padding: 10px; background-color: #f9f9f9; border-left: 4px solid #0066cc; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #0066cc; color: white; text-decoration: none; border-radius: 4px; margin-top: 10px; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #999; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚨 SRE Incident Alert</h1>
            <p>Your incident report has been triaged and a ticket has been created.</p>
        </div>

        <div class="section">
            <div class="section-title">Incident Summary</div>
            <div class="value">
                <strong>{incident_title}</strong><br/>
                <span class="severity severity-{severity_class}">{severity}</span>
            </div>
        </div>

        <div class="section">
            <div class="section-title">Details</div>
            <div class="value">
                <strong>Affected Module:</strong> {affected_module}<br/>
                <strong>Confidence Score:</strong> {confidence_percent}<br/>
                <strong>Trace ID:</strong> <code>{trace_id}</code>
            </div>
        </div>

        <div class="section">
            <div class="section-title">Technical Summary</div>
            <div class="value">{technical_summary}</div>
        </div>

        <div class="section">
            <a href="{ticket_url}" class="button">View Ticket in Trello</a>
        </div>

        <div class="footer">
            <p>This is an automated message from the SRE triage system. Do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
"""


class NotifyAgent:
    """
    Notifies team and reporter about the incident.
    Sends Slack message to #incidents and email to reporter.
    """

    def __init__(self) -> None:
        """Initialize agent with settings."""
        self.settings = get_settings()
        self.slack_webhook_url = self.settings.slack_webhook_url
        self.sendgrid_api_key = self.settings.sendgrid_api_key
        self.reporter_email_from = self.settings.reporter_email_from
        self.mock_integrations = self.settings.mock_integrations
        self.mock_email = self.settings.mock_email

    def process(self, incident_id: int, trace_id: str) -> Optional[dict[str, Any]]:
        """
        Send notifications to Slack and Email.

        Args:
            incident_id: ID of incident
            trace_id: Trace ID for observability

        Returns:
            Dictionary with notification info or None on error
        """
        start_time = time.monotonic()
        notifications_sent = []
        notification_failures = []

        try:
            # ── 1️⃣ Read incident, triage, and ticket from database ──────────
            with get_db() as db:
                incident = (
                    db.query(IncidentModel)
                    .filter(IncidentModel.id == incident_id)
                    .first()
                )
                if not incident:
                    logger.error(f"[{trace_id}] Incident not found: {incident_id}")
                    self._emit_error_event(
                        trace_id, incident_id, "incident_not_found", start_time
                    )
                    return None

                triage_result = (
                    db.query(TriageResultModel)
                    .filter(TriageResultModel.incident_id == incident_id)
                    .first()
                )
                if not triage_result:
                    logger.error(f"[{trace_id}] Triage result not found: {incident_id}")
                    self._emit_error_event(
                        trace_id, incident_id, "triage_result_not_found", start_time
                    )
                    return None

                ticket = (
                    db.query(TicketModel)
                    .filter(TicketModel.incident_id == incident_id)
                    .first()
                )
                if not ticket:
                    logger.warning(f"[{trace_id}] Ticket not found (yet), waiting...")
                    import time as time_module
                    time_module.sleep(0.5)
                    ticket = (
                        db.query(TicketModel)
                        .filter(TicketModel.incident_id == incident_id)
                        .first()
                    )

                if not ticket:
                    logger.error(
                        f"[{trace_id}] Ticket still not found after wait: {incident_id}"
                    )
                    self._emit_error_event(
                        trace_id, incident_id, "ticket_not_found", start_time
                    )
                    return None

                # Extract attributes while session is open
                incident_title = incident.title
                incident_description = incident.description
                reporter_email = incident.reporter_email
                severity = triage_result.severity
                affected_module = triage_result.affected_module
                technical_summary = triage_result.technical_summary
                confidence_score = triage_result.confidence_score
                ticket_id = ticket.id
                card_url = ticket.trello_card_url
                card_id = ticket.trello_card_id

            # ── 2️⃣ Send Slack notification ──────────────────────────────────
            slack_success = self._send_slack(
                incident_title,
                severity,
                affected_module,
                confidence_score,
                card_url,
                card_id,
                trace_id,
                reporter_email,
            )
            if slack_success:
                notifications_sent.append(NotificationChannel.SLACK.value)
            else:
                notification_failures.append(NotificationChannel.SLACK.value)

            # ── 3️⃣ Send Email notification ──────────────────────────────────
            email_success = self._send_email(
                incident_id,
                incident_title,
                incident_description,
                severity,
                affected_module,
                technical_summary,
                confidence_score,
                ticket_id,
                card_url,
                trace_id,
                reporter_email,
            )
            if email_success:
                notifications_sent.append(NotificationChannel.EMAIL.value)
            else:
                notification_failures.append(NotificationChannel.EMAIL.value)

            # ── 4️⃣ Update incident status to NOTIFIED ──────────────────────
            with get_db() as db:
                incident_model = (
                    db.query(IncidentModel)
                    .filter(IncidentModel.id == incident_id)
                    .first()
                )
                if incident_model:
                    incident_model.status = IncidentStatus.NOTIFIED.value
                    db.commit()

            # ── 5️⃣ Emit success/partial event with metadata ────────────────
            duration_ms = int((time.monotonic() - start_time) * 1000)

            # Determine overall status: success if all sent, error if all failed, partial mix
            if not notification_failures:
                overall_status = ObservabilityStatus.SUCCESS
            elif not notifications_sent:
                overall_status = ObservabilityStatus.ERROR
            else:
                overall_status = ObservabilityStatus.SUCCESS  # At least one succeeded

            metadata = {
                "notifications_sent": notifications_sent,
                "notifications_failed": notification_failures,
                "ticket_id": ticket_id,
                "card_url": card_url,
                "reporter_email": reporter_email if not notification_failures else None,
            }

            emit_event(
                trace_id=trace_id,
                stage=ObservabilityStage.NOTIFY,
                status=overall_status,
                duration_ms=duration_ms,
                incident_id=incident_id,
                metadata=metadata,
            )

            logger.info(
                f"[{trace_id}] Notifications sent:"
                f" slack={slack_success}"
                f" email={email_success}"
            )

            return {
                "incident_id": incident_id,
                "trace_id": trace_id,
                "notifications_sent": notifications_sent,
                "notifications_failed": notification_failures,
            }

        except Exception as exc:
            logger.exception(f"[{trace_id}] NotifyAgent error: {exc}")
            self._emit_error_event(trace_id, incident_id, str(exc), start_time)
            return None

    def _send_slack(
        self,
        incident_title: str,
        severity: str,
        affected_module: str,
        confidence_score: float,
        card_url: str,
        card_id: str,
        trace_id: str,
        reporter_email: str,
    ) -> bool:
        """
        Send Slack webhook notification.

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.slack_webhook_url:
                logger.warning("Slack webhook URL not configured")
                return False

            if self.mock_integrations:
                logger.info(f"[MOCK] Slack notification: {incident_title}")
                self._log_notification(
                    incident_id=None,
                    channel=NotificationChannel.SLACK.value,
                    recipient="#incidents",
                    notification_type=NotificationType.TEAM_ALERT.value,
                    content_summary=incident_title,
                    status=NotificationStatus.MOCKED.value,
                )
                return True

            # Severity emoji mapping
            severity_emoji = {
                "P1": "🔴",
                "P2": "🟠",
                "P3": "🟡",
                "P4": "🟢",
            }

            emoji = severity_emoji.get(severity, "⚠️")

            # Build Slack message
            slack_message = {
                "text": f"{emoji} Incident Report [{severity}] {incident_title}",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"{emoji} Incident Alert [{severity}]",
                        },
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{incident_title}*\n"
                            f"Module: `{affected_module}`\n"
                            f"Confidence: {confidence_score:.0%}\n"
                            f"Reporter: {reporter_email}\n"
                            f"Trace: `{trace_id}`",
                        },
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "View Ticket",
                                },
                                "url": card_url,
                                "style": (
                                    "danger"
                                    if severity == "P1"
                                    else "primary"
                                ),
                            }
                        ],
                    },
                ],
            }

            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    self.slack_webhook_url,
                    json=slack_message,
                )

            if response.status_code != 200:
                logger.error(
                    f"Slack API error ({response.status_code}): {response.text}"
                )
                self._log_notification(
                    incident_id=None,
                    channel=NotificationChannel.SLACK.value,
                    recipient="#incidents",
                    notification_type=NotificationType.TEAM_ALERT.value,
                    content_summary=incident_title,
                    status=NotificationStatus.FAILED.value,
                    error_message=response.text[:500],
                )
                return False

            logger.info("Slack notification sent successfully")
            self._log_notification(
                incident_id=None,
                channel=NotificationChannel.SLACK.value,
                recipient="#incidents",
                notification_type=NotificationType.TEAM_ALERT.value,
                content_summary=incident_title[:200],
                status=NotificationStatus.SENT.value,
            )
            return True

        except Exception as exc:
            logger.exception(f"Slack notification failed: {exc}")
            self._log_notification(
                incident_id=None,
                channel=NotificationChannel.SLACK.value,
                recipient="#incidents",
                notification_type=NotificationType.TEAM_ALERT.value,
                content_summary=incident_title[:200],
                status=NotificationStatus.FAILED.value,
                error_message=str(exc)[:500],
            )
            return False

    def _send_email(
        self,
        incident_id: int,
        incident_title: str,
        incident_description: str,
        severity: str,
        affected_module: str,
        technical_summary: str,
        confidence_score: float,
        ticket_id: int,
        card_url: str,
        trace_id: str,
        reporter_email: str,
    ) -> bool:
        """
        Send email notification via SendGrid or mock.

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.mock_integrations or self.mock_email or not self.sendgrid_api_key:
                logger.info(
                    f"[MOCK] Email notification to {reporter_email}: {incident_title}"
                )
                self._log_notification(
                    incident_id=incident_id,
                    channel=NotificationChannel.EMAIL.value,
                    recipient=reporter_email,
                    notification_type=NotificationType.REPORTER_CONFIRMATION.value,
                    content_summary=incident_title,
                    status=NotificationStatus.MOCKED.value,
                )
                return True

            # Build email HTML
            severity_class = severity.lower()
            confidence_percent = f"{confidence_score:.0%}"
            html_body = EMAIL_TEMPLATE.format(
                incident_title=incident_title,
                severity=severity,
                severity_class=severity_class,
                affected_module=affected_module,
                confidence_percent=confidence_percent,
                technical_summary=technical_summary,
                ticket_url=card_url,
                trace_id=trace_id,
            )

            # SendGrid API request
            url = "https://api.sendgrid.com/v3/mail/send"
            headers = {
                "Authorization": f"Bearer {self.sendgrid_api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "personalizations": [
                    {
                        "to": [{"email": reporter_email}],
                        "subject": f"[SRE Alert] Your incident report - Ticket #{ticket_id}",
                    }
                ],
                "from": {"email": self.reporter_email_from},
                "content": [
                    {
                        "type": "text/html",
                        "value": html_body,
                    }
                ],
            }

            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, json=payload, headers=headers)

            if response.status_code not in (200, 201, 202):
                logger.error(
                    f"SendGrid API error ({response.status_code}): {response.text}"
                )
                self._log_notification(
                    incident_id=incident_id,
                    channel=NotificationChannel.EMAIL.value,
                    recipient=reporter_email,
                    notification_type=NotificationType.REPORTER_CONFIRMATION.value,
                    content_summary=incident_title[:200],
                    status=NotificationStatus.FAILED.value,
                    error_message=response.text[:500],
                )
                return False

            logger.info(f"Email sent to {reporter_email}")
            self._log_notification(
                incident_id=incident_id,
                channel=NotificationChannel.EMAIL.value,
                recipient=reporter_email,
                notification_type=NotificationType.REPORTER_CONFIRMATION.value,
                content_summary=incident_title[:200],
                status=NotificationStatus.SENT.value,
            )
            return True

        except Exception as exc:
            logger.exception(f"Email notification failed: {exc}")
            self._log_notification(
                incident_id=incident_id,
                channel=NotificationChannel.EMAIL.value,
                recipient=reporter_email,
                notification_type=NotificationType.REPORTER_CONFIRMATION.value,
                content_summary=incident_title[:200],
                status=NotificationStatus.FAILED.value,
                error_message=str(exc)[:500],
            )
            return False

    def _log_notification(
        self,
        channel: str,
        recipient: str,
        notification_type: str,
        content_summary: str,
        status: str,
        incident_id: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Persist notification log to database."""
        try:
            with get_db() as db:
                log = NotificationLogModel(
                    incident_id=incident_id,
                    channel=channel,
                    recipient=recipient,
                    notification_type=notification_type,
                    content_summary=content_summary,
                    status=status,
                    error_message=error_message,
                )
                db.add(log)
        except Exception as exc:
            logger.warning(f"Failed to log notification: {exc}")

    def _emit_error_event(
        self,
        trace_id: str,
        incident_id: Optional[int],
        error_msg: str,
        start_time: Optional[float] = None,
    ) -> None:
        """Helper to emit error observability event."""
        duration_ms = 0
        if start_time is not None:
            duration_ms = int((time.monotonic() - start_time) * 1000)

        try:
            emit_event(
                trace_id=trace_id,
                stage=ObservabilityStage.NOTIFY,
                status=ObservabilityStatus.ERROR,
                duration_ms=duration_ms,
                incident_id=incident_id,
                metadata={"error": error_msg},
            )
        except Exception as exc:
            logger.warning(f"Failed to emit error event: {exc}")

    def send_resolution_email(
        self,
        incident_id: int,
        trace_id: str,
        ticket_url: str,
        reporter_email: str,
    ) -> dict[str, Any]:
        """
        Send resolution notification email to reporter.

        Called by ResolutionWatcher when a ticket is marked as resolved.

        Args:
            incident_id: ID of incident
            trace_id: Trace ID for observability
            ticket_url: URL of the Trello card (for reference)
            reporter_email: Email address of the reporter

        Returns:
            Dictionary with {"status": "sent" | "failed", "error": "..."}
        """
        try:
            if self.mock_email:
                logger.info(
                    f"[{trace_id}] [MOCK] Resolution email to {reporter_email}"
                )
                self._log_notification(
                    incident_id=incident_id,
                    channel=NotificationChannel.EMAIL.value,
                    recipient=reporter_email,
                    notification_type=NotificationType.REPORTER_RESOLUTION.value,
                    content_summary="Incident resolved",
                    status=NotificationStatus.MOCKED.value,
                )
                return {"status": "sent"}

            if self.mock_integrations:
                logger.info(
                    f"[{trace_id}] [MOCK] Resolution email to {reporter_email}"
                )
                self._log_notification(
                    incident_id=incident_id,
                    channel=NotificationChannel.EMAIL.value,
                    recipient=reporter_email,
                    notification_type=NotificationType.REPORTER_RESOLUTION.value,
                    content_summary="Incident resolved",
                    status=NotificationStatus.MOCKED.value,
                )
                return {"status": "sent"}

            if not self.sendgrid_api_key:
                logger.warning(f"[{trace_id}] SendGrid API key not configured")
                self._log_notification(
                    incident_id=incident_id,
                    channel=NotificationChannel.EMAIL.value,
                    recipient=reporter_email,
                    notification_type=NotificationType.REPORTER_RESOLUTION.value,
                    content_summary="Incident resolved",
                    status=NotificationStatus.FAILED.value,
                    error_message="SendGrid not configured",
                )
                return {"status": "failed", "error": "sendgrid_not_configured"}

            # Build resolution email HTML
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4CAF50; padding: 20px; border-radius: 8px; margin-bottom: 20px; color: white; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .section {{ margin: 20px 0; }}
        .section-title {{ font-weight: bold; font-size: 14px; color: #333; margin-bottom: 10px; }}
        .value {{ color: #666; padding: 10px; background-color: #f9f9f9; border-left: 4px solid #4CAF50; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px; margin-top: 10px; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #999; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✅ Incident Resolved</h1>
            <p>Your incident report has been resolved.</p>
        </div>

        <div class="section">
            <div class="section-title">Good News!</div>
            <div class="value">
                The incident you reported has been resolved by the SRE team.
                The ticket has been moved to the Done column in our tracking system.
            </div>
        </div>

        <div class="section">
            <div class="section-title">Details</div>
            <div class="value">
                <strong>Trace ID:</strong> <code>{trace_id}</code><br/>
                <strong>Resolution Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
            </div>
        </div>

        <div class="section">
            <a href="{ticket_url}" class="button">View Resolution Details</a>
        </div>

        <div class="section">
            <div class="section-title">Next Steps</div>
            <div class="value">
                If you notice any issues related to this incident please open a new report.
                Thank you for helping us maintain system reliability.
            </div>
        </div>

        <div class="footer">
            <p>This is an automated message from the SRE triage system. Do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
"""

            # SendGrid API request
            url = "https://api.sendgrid.com/v3/mail/send"
            headers = {
                "Authorization": f"Bearer {self.sendgrid_api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "personalizations": [
                    {
                        "to": [{"email": reporter_email}],
                        "subject": f"✅ Incident Resolved - Trace {trace_id[:8]}",
                    }
                ],
                "from": {"email": self.reporter_email_from},
                "content": [
                    {
                        "type": "text/html",
                        "value": html_content,
                    }
                ],
            }

            logger.info(
                f"[{trace_id}] Sending resolution email to {reporter_email}"
            )

            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, json=payload, headers=headers)

            if response.status_code not in (200, 201, 202):
                logger.error(
                    f"[{trace_id}] SendGrid error ({response.status_code}): "
                    f"{response.text[:200]}"
                )
                self._log_notification(
                    incident_id=incident_id,
                    channel=NotificationChannel.EMAIL.value,
                    recipient=reporter_email,
                    notification_type=NotificationType.REPORTER_RESOLUTION.value,
                    content_summary="Incident resolved",
                    status=NotificationStatus.FAILED.value,
                    error_message=response.text[:500],
                )
                return {"status": "failed", "error": response.text[:200]}

            logger.info(
                f"[{trace_id}] Resolution email sent successfully to {reporter_email}"
            )
            self._log_notification(
                incident_id=incident_id,
                channel=NotificationChannel.EMAIL.value,
                recipient=reporter_email,
                notification_type=NotificationType.REPORTER_RESOLUTION.value,
                content_summary="Incident resolved",
                status=NotificationStatus.SENT.value,
            )
            return {"status": "sent"}

        except Exception as exc:
            logger.exception(f"[{trace_id}] Resolution email failed: {exc}")
            self._log_notification(
                incident_id=incident_id,
                channel=NotificationChannel.EMAIL.value,
                recipient=reporter_email,
                notification_type=NotificationType.REPORTER_RESOLUTION.value,
                content_summary="Incident resolved",
                status=NotificationStatus.FAILED.value,
                error_message=str(exc)[:500],
            )
            return {"status": "failed", "error": str(exc)}
