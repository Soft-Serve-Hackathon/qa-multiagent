"""
Resolution Watcher Agent.

Background polling task that monitors Trello cards for resolution.
When a card moves to "Done" column, marks ticket as resolved and notifies the reporter.

Runs in a separate async task within FastAPI lifespan, polling every 60 seconds.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, Optional

import httpx

from ..config import get_settings
from ..domain.enums import (
    IncidentStatus,
    NotificationStatus,
    ObservabilityStage,
    ObservabilityStatus,
)
from ..infrastructure.database import (
    IncidentModel,
    NotificationLogModel,
    TicketModel,
    get_db,
)
from ..infrastructure.observability.events import emit_event
from .notify_agent import NotifyAgent

logger = logging.getLogger(__name__)


class ResolutionWatcher:
    """
    Monitors Trello cards for resolution and completes the incident lifecycle.

    Runs as a background task polling unresolved tickets every 60 seconds.
    When a card is found in the "Done" column:
    1. Updates ticket.resolved_at in database
    2. Updates incident.status to 'resolved'
    3. Sends resolution email to reporter via NotifyAgent
    4. Emits observability event for full traceability
    """

    def __init__(self) -> None:
        """Initialize watcher with settings and Trello API client."""
        self.settings = get_settings()
        self.trello_api_key = self.settings.trello_api_key
        self.trello_api_token = self.settings.trello_api_token
        self.trello_done_list_id = self.settings.trello_done_list_id
        self.poll_interval = self.settings.resolution_watcher_interval_seconds
        self.mock_integrations = self.settings.mock_integrations
        self.base_url = "https://api.trello.com/1"

        self.notify_agent = NotifyAgent()
        self._stop_event: Optional[asyncio.Event] = None
        self._polling_task: Optional[asyncio.Task] = None
        self._iteration_count = 0

    async def start(self) -> None:
        """
        Start the background polling loop.

        Called from FastAPI lifespan startup.
        Creates async task that will run independently.
        """
        self._stop_event = asyncio.Event()
        self._polling_task = asyncio.create_task(self._polling_loop())
        logger.info(f"ResolutionWatcher started (poll interval: {self.poll_interval}s)")

    async def stop(self) -> None:
        """
        Gracefully stop the polling loop.

        Called from FastAPI lifespan shutdown.
        Sets stop event and waits for polling task to complete.
        Handles case where polling is not running.
        """
        if self._stop_event is None or self._polling_task is None:
            logger.warning("ResolutionWatcher was not started")
            return

        logger.info("ResolutionWatcher stopping...")
        self._stop_event.set()

        try:
            await self._polling_task
            logger.info("ResolutionWatcher stopped gracefully")
        except asyncio.CancelledError:
            logger.info("ResolutionWatcher polling task cancelled")
        except Exception as exc:
            logger.error(f"Error stopping ResolutionWatcher: {exc}")

    async def _polling_loop(self) -> None:
        """
        Main polling loop that runs every poll_interval seconds.

        Continues until stop() is called via stop event.
        Catches exceptions to ensure loop never crashes.
        """
        while not self._stop_event.is_set():
            try:
                self._iteration_count += 1
                await self._poll_once()
            except Exception as exc:
                logger.exception(
                    f"ResolutionWatcher polling iteration error: {exc}"
                )

            # Wait poll_interval seconds or until stop signal
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self.poll_interval,
                )
                # If we reach here, stop was called
                break
            except asyncio.TimeoutError:
                # Timeout means continue polling
                pass

    async def _poll_once(self) -> None:
        """
        Single iteration of polling: fetch unresolved tickets and check Trello status.

        Steps:
        1. Query database for all unresolved tickets
        2. For each ticket, fetch card status from Trello
        3. If card is in "Done" column:
           - Mark ticket.resolved_at in DB
           - Update incident.status = 'resolved'
           - Notify reporter via email
           - Emit observability event
        """
        unresolved_tickets = self._get_unresolved_tickets()

        if not unresolved_tickets:
            logger.debug(
                f"ResolutionWatcher iteration #{self._iteration_count}: "
                "no unresolved tickets"
            )
            return

        logger.info(
            f"ResolutionWatcher iteration #{self._iteration_count}: "
            f"found {len(unresolved_tickets)} unresolved tickets"
        )

        for ticket in unresolved_tickets:
            await self._check_and_resolve_ticket(ticket)

    def _get_unresolved_tickets(self) -> list[TicketModel]:
        """
        Fetch all tickets that are not yet resolved.

        A ticket is considered unresolved if resolved_at IS NULL.

        Returns:
            List of TicketModel objects, may be empty
        """
        try:
            with get_db() as db:
                tickets = (
                    db.query(TicketModel)
                    .filter(TicketModel.resolved_at.is_(None))
                    .all()
                )
                return tickets
        except Exception as exc:
            logger.error(f"Error fetching unresolved tickets: {exc}")
            return []

    async def _check_and_resolve_ticket(self, ticket: TicketModel) -> None:
        """
        Check if a ticket's Trello card is Done and resolve if so.

        Args:
            ticket: TicketModel instance to check
        """
        start_time = time.monotonic()

        try:
            # Get incident for trace_id and reporter email
            with get_db() as db:
                incident = (
                    db.query(IncidentModel)
                    .filter(IncidentModel.id == ticket.incident_id)
                    .first()
                )
                if not incident:
                    logger.warning(
                        f"Incident not found for ticket {ticket.id}: "
                        f"incident_id={ticket.incident_id}"
                    )
                    return

                trace_id = incident.trace_id
                reporter_email = incident.reporter_email
                card_id = ticket.trello_card_id

            logger.debug(
                f"[{trace_id}] Checking Trello card status: {card_id}"
            )

            # ── 1️⃣ Fetch card status from Trello ────────────────────────
            card_is_done = await self._is_card_done(card_id, trace_id)

            if not card_is_done:
                logger.debug(f"[{trace_id}] Card {card_id} not in Done column")
                return

            logger.info(f"[{trace_id}] Card {card_id} is DONE, resolving...")

            # ── 2️⃣ Mark ticket as resolved in database ──────────────────
            with get_db() as db:
                ticket_model = (
                    db.query(TicketModel)
                    .filter(TicketModel.id == ticket.id)
                    .first()
                )
                if ticket_model:
                    ticket_model.resolved_at = datetime.utcnow()
                    db.commit()
                    logger.debug(
                        f"[{trace_id}] Ticket {ticket.id} marked resolved_at"
                    )

            # ── 3️⃣ Update incident status to RESOLVED ─────────────────
            with get_db() as db:
                incident_model = (
                    db.query(IncidentModel)
                    .filter(IncidentModel.id == ticket.incident_id)
                    .first()
                )
                if incident_model:
                    incident_model.status = IncidentStatus.RESOLVED.value
                    db.commit()
                    logger.debug(
                        f"[{trace_id}] Incident {ticket.incident_id} "
                        f"status set to {IncidentStatus.RESOLVED.value}"
                    )

            # ── 4️⃣ Notify reporter that incident is resolved ──────────────
            notification_status = await self._send_resolution_notification(
                trace_id, ticket, reporter_email
            )

            # ── 5️⃣ Emit observability event (stage=resolved) ──────────────
            duration_ms = int((time.monotonic() - start_time) * 1000)

            emit_event(
                trace_id=trace_id,
                stage=ObservabilityStage.RESOLVED,
                status=ObservabilityStatus.SUCCESS,
                duration_ms=duration_ms,
                incident_id=ticket.incident_id,
                metadata={
                    "ticket_id": ticket.id,
                    "trello_card_id": card_id,
                    "notification_sent": notification_status == "sent",
                },
            )

            logger.info(
                f"[{trace_id}] Incident resolved: ticket={ticket.id} "
                f"notification={notification_status}"
            )

        except Exception as exc:
            logger.exception(
                f"Error checking ticket {ticket.id}: {exc}"
            )
            # Emit error event with what we have
            try:
                with get_db() as db:
                    incident = (
                        db.query(IncidentModel)
                        .filter(IncidentModel.id == ticket.incident_id)
                        .first()
                    )
                    trace_id = incident.trace_id if incident else "unknown"

                duration_ms = int((time.monotonic() - start_time) * 1000)
                emit_event(
                    trace_id=trace_id,
                    stage=ObservabilityStage.RESOLVED,
                    status=ObservabilityStatus.ERROR,
                    duration_ms=duration_ms,
                    incident_id=ticket.incident_id,
                    metadata={"error": str(exc)},
                )
            except Exception as emit_exc:
                logger.error(f"Failed to emit error event: {emit_exc}")

    async def _is_card_done(self, card_id: str, trace_id: str) -> bool:
        """
        Check if a Trello card is in the "Done" list.

        Args:
            card_id: Trello card ID
            trace_id: Trace ID for logging

        Returns:
            True if card is in Done list, False otherwise
        """
        try:
            if self.mock_integrations:
                logger.debug(f"[{trace_id}] [MOCK] Checking card {card_id}")
                return False

            if not self.trello_api_key or not self.trello_api_token:
                logger.error(f"[{trace_id}] Trello credentials not configured")
                return False

            params = {
                "key": self.trello_api_key,
                "token": self.trello_api_token,
            }

            url = f"{self.base_url}/cards/{card_id}"

            logger.debug(f"[{trace_id}] Fetching card: GET {url}")

            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params)

            if response.status_code != 200:
                logger.warning(
                    f"[{trace_id}] Trello API error ({response.status_code}): "
                    f"{response.text[:200]}"
                )
                return False

            card_data = response.json()
            card_list_id = card_data.get("idList")

            is_done = card_list_id == self.trello_done_list_id

            logger.debug(
                f"[{trace_id}] Card {card_id} list: {card_list_id}"
                f" (done_list: {self.trello_done_list_id})"
                f" → is_done={is_done}"
            )

            return is_done

        except Exception as exc:
            logger.error(f"[{trace_id}] Error checking card {card_id}: {exc}")
            return False

    async def _send_resolution_notification(
        self,
        trace_id: str,
        ticket: TicketModel,
        reporter_email: str,
    ) -> str:
        """
        Send resolution email notification to reporter.

        Delegates to NotifyAgent but wraps with error handling.

        Args:
            trace_id: Trace ID for logging
            ticket: TicketModel with resolved card
            reporter_email: Reporter email address

        Returns:
            "sent" if successful, "failed" otherwise
        """
        try:
            result = self.notify_agent.send_resolution_email(
                incident_id=ticket.incident_id,
                trace_id=trace_id,
                ticket_url=ticket.trello_card_url,
                reporter_email=reporter_email,
            )

            if result and result.get("status") == "sent":
                logger.info(
                    f"[{trace_id}] Resolution email sent to {reporter_email}"
                )
                return "sent"
            else:
                logger.warning(
                    f"[{trace_id}] Resolution email notification failed: "
                    f"{result}"
                )
                return "failed"

        except Exception as exc:
            logger.error(
                f"[{trace_id}] Error sending resolution notification: {exc}"
            )
            return "failed"
