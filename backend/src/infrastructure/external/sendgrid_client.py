"""SendGrid email client — confirmation and resolution emails to reporters."""
import requests
from src.config import settings
from src.domain.value_objects import SEVERITY_SLA_HOURS

SENDGRID_API = "https://api.sendgrid.com/v3/mail/send"


class SendGridClient:
    def __init__(self):
        self._api_key = settings.SENDGRID_API_KEY
        self._from_email = settings.SENDGRID_FROM_EMAIL
        self._from_name = settings.SENDGRID_FROM_NAME
        self._mock = settings.MOCK_INTEGRATIONS

    def send_confirmation(
        self,
        to_email: str,
        incident_title: str,
        severity: str,
        trello_card_id: str,
        trello_card_url: str,
    ) -> bool:
        """Send incident acknowledgement email to the reporter."""
        sla = SEVERITY_SLA_HOURS.get(severity, 24)
        subject = f"[Incident received] {incident_title} — Ref: TRELLO-{trello_card_id[:8]}"
        body = (
            f"Hi,\n\n"
            f"We've received your incident report and created a ticket to track it.\n\n"
            f"Incident: {incident_title}\n"
            f"Reference: TRELLO-{trello_card_id}\n"
            f"Severity: {severity} — Expected response time: < {sla} hour{'s' if sla != 1 else ''}\n"
            f"Ticket link: {trello_card_url}\n\n"
            f"Our team has been notified and is working on it.\n"
            f"We will let you know when the issue is resolved.\n\n"
            f"SRE Team"
        )
        return self._send(to_email, subject, body)

    def send_resolution(
        self,
        to_email: str,
        incident_title: str,
        trello_card_id: str,
        trello_card_url: str,
        resolved_at: str,
    ) -> bool:
        """Send resolution notification email to the reporter."""
        subject = f"[Resolved] {incident_title} — Ref: TRELLO-{trello_card_id[:8]}"
        body = (
            f"Hi,\n\n"
            f"Your incident report has been resolved.\n\n"
            f"Incident: {incident_title}\n"
            f"Reference: TRELLO-{trello_card_id}\n"
            f"Resolved at: {resolved_at}\n\n"
            f"Thank you for reporting. Let us know if the issue persists.\n\n"
            f"SRE Team"
        )
        return self._send(to_email, subject, body)

    def _send(self, to_email: str, subject: str, body: str) -> bool:
        if self._mock:
            return True
        if not self._api_key:
            return False
        payload = {
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": self._from_email, "name": self._from_name},
            "subject": subject,
            "content": [{"type": "text/plain", "value": body}],
        }
        try:
            resp = requests.post(
                SENDGRID_API,
                json=payload,
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=10,
            )
            return resp.status_code in (200, 202)
        except Exception:
            return False
