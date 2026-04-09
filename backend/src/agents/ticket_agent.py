"""
Ticket Agent.

Creates Trello cards based on triage results.
Implements intelligent deduplication: checks for similar existing tickets before
creating new ones. If similarity >= 75%, links to the existing ticket instead.
Persists ticket information and emits observability events.
Handles Trello API integration with robust error handling.
"""

import json
import logging
import time
from difflib import SequenceMatcher
from typing import Any, Optional

import httpx

from ..config import get_settings
from ..domain.enums import (
    IncidentStatus,
    ObservabilityStage,
    ObservabilityStatus,
    Severity,
    TicketStatus,
)
from ..infrastructure.database import (
    IncidentModel,
    TicketModel,
    TriageResultModel,
    get_db,
)
from ..infrastructure.observability.events import emit_event

logger = logging.getLogger(__name__)

# Trello severity to label mapping
SEVERITY_TO_LABEL = {
    Severity.P1.value: "P1-Critical",
    Severity.P2.value: "P2-High",
    Severity.P3.value: "P3-Medium",
    Severity.P4.value: "P4-Low",
}

# Similarity threshold for deduplication (75% match = duplicate)
DEDUP_THRESHOLD = 0.75
# Only compare against tickets from the last N incidents (performance guard)
DEDUP_LOOKBACK = 20


def _string_similarity(a: str, b: str) -> float:
    """Compute normalized similarity ratio between two strings (0.0–1.0)."""
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


class TicketDeduplicator:
    """
    Finds existing open tickets that are semantically similar to a new incident.

    Algorithm:
    - Retrieve last DEDUP_LOOKBACK tickets for the same affected module
    - Compute weighted similarity: 60% title + 40% description (first 200 chars)
    - Return the most similar ticket if score >= DEDUP_THRESHOLD, else None
    """

    def find_similar_ticket(
        self,
        incident_title: str,
        incident_description: str,
        affected_module: str,
        threshold: float = DEDUP_THRESHOLD,
    ) -> Optional[tuple["TicketModel", float]]:
        """
        Search for a similar existing open ticket.

        Returns:
            (TicketModel, similarity_score) if found, else None
        """
        with get_db() as db:
            # Fetch recent tickets for same module (not resolved)
            candidates = (
                db.query(TicketModel, IncidentModel, TriageResultModel)
                .join(IncidentModel, TicketModel.incident_id == IncidentModel.id)
                .join(TriageResultModel, TriageResultModel.incident_id == IncidentModel.id)
                .filter(TriageResultModel.affected_module == affected_module)
                .filter(TicketModel.status != TicketStatus.FAILED.value)
                .order_by(TicketModel.created_at.desc())
                .limit(DEDUP_LOOKBACK)
                .all()
            )

            best_ticket: Optional[TicketModel] = None
            best_score: float = 0.0

            for ticket, incident, _ in candidates:
                title_sim = _string_similarity(incident_title, incident.title)
                desc_sim = _string_similarity(
                    incident_description[:200],
                    incident.description[:200],
                )
                combined = (title_sim * 0.6) + (desc_sim * 0.4)

                logger.debug(
                    f"Dedup check: existing_ticket={ticket.id} "
                    f"title_sim={title_sim:.2f} desc_sim={desc_sim:.2f} "
                    f"combined={combined:.2f}"
                )

                if combined > best_score:
                    best_score = combined
                    best_ticket = ticket

        if best_ticket and best_score >= threshold:
            return best_ticket, best_score

        return None


class TicketAgent:
    """
    Creates Trello cards from triage results.
    Coordinates with Trello REST API and persists ticket references.
    """

    def __init__(self) -> None:
        """Initialize agent with settings."""
        self.settings = get_settings()
        self.trello_api_key = self.settings.trello_api_key
        self.trello_api_token = self.settings.trello_api_token
        self.trello_list_id = self.settings.trello_list_id
        self.mock_integrations = self.settings.mock_integrations
        self.base_url = "https://api.trello.com/1"

    def process(self, incident_id: int, trace_id: str) -> Optional[dict[str, Any]]:
        """
        Create a Trello card from triage result.

        Args:
            incident_id: ID of incident to ticket
            trace_id: Trace ID for observability

        Returns:
            Dictionary with ticket info or None on error
        """
        start_time = time.monotonic()

        try:
            # ── 1️⃣ Read incident and triage result from database ────────────
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

                # Extract attributes while session is open
                incident_title = incident.title
                incident_description = incident.description
                severity = triage_result.severity
                affected_module = triage_result.affected_module
                technical_summary = triage_result.technical_summary
                suggested_files = triage_result.get_suggested_files()
                confidence_score = triage_result.confidence_score

            # ── 2️⃣ Deduplication check ───────────────────────────────────
            deduplicator = TicketDeduplicator()
            dedup_result = deduplicator.find_similar_ticket(
                incident_title=incident_title,
                incident_description=incident_description,
                affected_module=affected_module,
            )

            if dedup_result is not None:
                existing_ticket, similarity_score = dedup_result
                logger.info(
                    f"[{trace_id}] Duplicate detected: "
                    f"existing_ticket_id={existing_ticket.id} "
                    f"similarity={similarity_score:.1%} — skipping new card creation"
                )

                # Link this incident to the existing ticket
                with get_db() as db:
                    incident_model = (
                        db.query(IncidentModel)
                        .filter(IncidentModel.id == incident_id)
                        .first()
                    )
                    if incident_model:
                        incident_model.status = IncidentStatus.DEDUPLICATED.value
                        incident_model.linked_ticket_id = existing_ticket.id
                        db.commit()

                duration_ms = int((time.monotonic() - start_time) * 1000)
                emit_event(
                    trace_id=trace_id,
                    stage=ObservabilityStage.TICKET,
                    status=ObservabilityStatus.DEDUPLICATED,
                    duration_ms=duration_ms,
                    incident_id=incident_id,
                    metadata={
                        "deduplicated": True,
                        "existing_ticket_id": existing_ticket.id,
                        "existing_card_id": existing_ticket.trello_card_id,
                        "existing_card_url": existing_ticket.trello_card_url,
                        "similarity_score": round(similarity_score, 3),
                        "affected_module": affected_module,
                    },
                )

                return {
                    "incident_id": incident_id,
                    "ticket_id": existing_ticket.id,
                    "card_id": existing_ticket.trello_card_id,
                    "card_url": existing_ticket.trello_card_url,
                    "trace_id": trace_id,
                    "deduplicated": True,
                    "similarity_score": similarity_score,
                }

            # ── 3️⃣ Build Trello card name and description ──────────────────
            card_name = f"[{severity}] {incident_title}"
            card_description = self._build_card_description(
                incident_description,
                severity,
                affected_module,
                technical_summary,
                suggested_files,
                confidence_score,
                trace_id,
            )

            logger.info(f"[{trace_id}] Building Trello card: {card_name}")

            # ── 3️⃣ Resolve severity label and module label ─────────────────
            severity_label = SEVERITY_TO_LABEL.get(
                severity, "P4-Low"
            )  # Fallback to P4
            module_label = f"module-{affected_module.lower()}"

            # ── 4️⃣ Create card via Trello API ────────────────────────────────
            if self.mock_integrations:
                card_id, card_url = self._create_card_mock(card_name, card_description)
            else:
                card_id, card_url = self._create_card_trello(
                    card_name,
                    card_description,
                    severity_label,
                    module_label,
                )

            if not card_id:
                logger.error(f"[{trace_id}] Failed to create Trello card")
                self._emit_error_event(
                    trace_id, incident_id, "trello_card_creation_failed", start_time
                )
                return None

            # ── 5️⃣ Persist ticket to database ───────────────────────────────
            with get_db() as db:
                ticket = TicketModel(
                    incident_id=incident_id,
                    trello_card_id=card_id,
                    trello_card_url=card_url,
                    trello_list_id=self.trello_list_id,
                    status=TicketStatus.PENDING.value,
                )
                db.add(ticket)
                db.flush()
                ticket_id = ticket.id

                # ── 6️⃣ Update incident status to NOTIFIED ─────────────────────
                # (Ready for next agent in pipeline)
                incident_model = (
                    db.query(IncidentModel)
                    .filter(IncidentModel.id == incident_id)
                    .first()
                )
                if incident_model:
                    incident_model.status = IncidentStatus.NOTIFIED.value
                    db.commit()

            # ── 7️⃣ Emit success event with metadata ──────────────────────────
            duration_ms = int((time.monotonic() - start_time) * 1000)

            metadata = {
                "ticket_id": ticket_id,
                "card_id": card_id,
                "card_url": card_url,
                "severity": severity,
                "module": affected_module,
                "labels": [severity_label, module_label],
                "confidence_score": confidence_score,
            }

            emit_event(
                trace_id=trace_id,
                stage=ObservabilityStage.TICKET,
                status=ObservabilityStatus.SUCCESS,
                duration_ms=duration_ms,
                incident_id=incident_id,
                metadata=metadata,
            )

            logger.info(
                f"[{trace_id}] Ticket created:"
                f" ticket_id={ticket_id}"
                f" card_id={card_id}"
                f" severity={severity}"
                f" module={affected_module}"
            )

            return {
                "incident_id": incident_id,
                "ticket_id": ticket_id,
                "card_id": card_id,
                "card_url": card_url,
                "trace_id": trace_id,
            }

        except Exception as exc:
            logger.exception(f"[{trace_id}] TicketAgent error: {exc}")
            self._emit_error_event(trace_id, incident_id, str(exc), start_time)
            return None

    def _build_card_description(
        self,
        incident_description: str,
        severity: str,
        affected_module: str,
        technical_summary: str,
        suggested_files: list[str],
        confidence_score: float,
        trace_id: str,
    ) -> str:
        """Build formatted Trello card description."""
        files_text = (
            "\n".join(f"- {f}" for f in suggested_files[:10])
            if suggested_files
            else "None identified"
        )

        description = (
            f"## Incident Report\n\n"
            f"**Original Description:**\n{incident_description[:500]}\n\n"
            f"**Severity:** {severity}\n"
            f"**Affected Module:** {affected_module}\n"
            f"**Confidence Score:** {confidence_score:.1%}\n\n"
            f"## Technical Analysis\n{technical_summary}\n\n"
            f"## Suggested Files\n{files_text}\n\n"
            f"**Trace ID:** `{trace_id}`"
        )

        return description

    def _create_card_trello(
        self,
        card_name: str,
        card_description: str,
        severity_label: str,
        module_label: str,
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Create card via Trello REST API.

        Returns:
            Tuple of (card_id, card_url) or (None, None) on failure
        """
        try:
            if not self.trello_api_key or not self.trello_api_token:
                logger.error("Trello credentials not configured")
                return None, None

            # Create label colors mapping (Trello standard colors)
            label_colors = {
                "P1-Critical": "red",
                "P2-High": "orange",
                "P3-Medium": "yellow",
                "P4-Low": "green",
            }

            params = {
                "key": self.trello_api_key,
                "token": self.trello_api_token,
            }

            # Prepare labels payload
            labels_payload = [
                {
                    "name": severity_label,
                    "color": label_colors.get(severity_label, "blue"),
                },
                {
                    "name": module_label,
                    "color": "purple",
                },
            ]

            payload = {
                "name": card_name,
                "desc": card_description,
                "idList": self.trello_list_id,
                "labels": labels_payload,
            }

            url = f"{self.base_url}/cards"

            logger.info(f"Creating Trello card: POST {url}")

            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, json=payload, params=params)

            if response.status_code != 200:
                logger.error(
                    f"Trello API error ({response.status_code}): {response.text}"
                )
                return None, None

            data = response.json()
            card_id = data.get("id")
            card_url = data.get("url")

            logger.info(f"Trello card created: {card_id} → {card_url}")

            return card_id, card_url

        except Exception as exc:
            logger.exception(f"Trello API request failed: {exc}")
            return None, None

    def _create_card_mock(
        self,
        card_name: str,
        card_description: str,
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Mock Trello card creation for testing/dev mode.

        Returns:
            Tuple of (card_id, card_url)
        """
        import uuid

        card_id = f"MOCK-{uuid.uuid4().hex[:8].upper()}"
        card_url = f"https://trello.com/c/{card_id}/mock-card"

        logger.info(f"[MOCK] Trello card created: {card_id} → {card_url}")
        logger.debug(f"[MOCK] Card name: {card_name}")
        logger.debug(f"[MOCK] Card description: {card_description[:200]}...")

        return card_id, card_url

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
                stage=ObservabilityStage.TICKET,
                status=ObservabilityStatus.ERROR,
                duration_ms=duration_ms,
                incident_id=incident_id,
                metadata={"error": error_msg},
            )
        except Exception as exc:
            logger.warning(f"Failed to emit error event: {exc}")
