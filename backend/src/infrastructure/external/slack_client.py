"""Slack incoming webhook client — posts incident notifications."""
import requests
from src.config import settings
from src.domain.value_objects import SEVERITY_EMOJI


class SlackClient:
    def __init__(self):
        self._webhook_url = settings.SLACK_WEBHOOK_URL
        self._mock = settings.MOCK_INTEGRATIONS

    def post_incident_alert(
        self,
        title: str,
        description: str,
        severity: str,
        affected_module: str,
        confidence: float,
        trello_url: str,
        trace_id: str,
        owner_slack_user_id: str | None = None,
    ) -> bool:
        """Post a new incident alert to Slack. Returns True on success."""
        emoji = SEVERITY_EMOJI.get(severity, ":white_circle:")
        mention = "@here " if severity == "P1" else ""
        owner_line = f"\n:technologist: Owner assigned: <@{owner_slack_user_id}>" if owner_slack_user_id else ""
        text = (
            f"{mention}*[{severity}] New incident: {title}*\n"
            f"> {description[:200]}{'...' if len(description) > 200 else ''}\n"
            f"{emoji} Severity: {severity} | Module: {affected_module} | Confidence: {int(confidence * 100)}%\n"
            f":trello: <{trello_url}|View Trello Card>\n"
            f"{owner_line}\n"
            f":mag: trace_id: `{trace_id}`"
        )
        return self._post(text)

    def post_resolution_notice(self, title: str, trello_url: str, trace_id: str) -> bool:
        """Post a resolution notice to Slack."""
        text = (
            f":white_check_mark: *Resolved: {title}*\n"
            f":trello: <{trello_url}|View Card>\n"
            f":mag: trace_id: `{trace_id}`"
        )
        return self._post(text)

    def _post(self, text: str) -> bool:
        if self._mock:
            # Log mock Slack message to observability
            import logging
            logger = logging.getLogger("mock-slack")
            logger.info(f"[MOCK SLACK 🎭] {text[:500]}")
            return True
        try:
            resp = requests.post(
                self._webhook_url,
                json={"text": text},
                timeout=10,
            )
            return resp.status_code == 200
        except Exception:
            return False
