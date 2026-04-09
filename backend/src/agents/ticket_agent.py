"""TicketAgent — creates a Trello card with triage summary and suggested files."""
import time
from sqlalchemy.orm import Session

from src.domain.entities import Incident, Ticket
from src.application.dto import TriageResultDTO, TicketDTO
from src.infrastructure.external.trello_client import TrelloClient
from src.infrastructure.observability.events import emit_event
from src.config import settings


class TicketAgent:
    """
    Responsibility: Build the Trello card payload and create the card.
    Persists Ticket entity. Updates Incident status to 'notified'.
    """

    def __init__(self, db: Session):
        self._db = db
        self._trello = TrelloClient()

    def process(self, triage: TriageResultDTO) -> TicketDTO:
        start = time.monotonic()
        incident: Incident = self._db.query(Incident).filter(Incident.id == triage.incident_id).first()

        card_title = f"[{triage.severity}] {incident.title}"
        files_list = "\n".join(f"- {f}" for f in triage.suggested_files) or "- No specific files identified"
        card_description = (
            f"## Technical Summary\n{triage.technical_summary}\n\n"
            f"## Affected Module\n{triage.affected_module} (confidence: {int(triage.confidence_score * 100)}%)\n\n"
            f"## Suggested Files to Investigate\n{files_list}\n\n"
            f"## Reporter\n{incident.reporter_email}\n\n"
            f"## Trace ID\n{triage.trace_id}"
        )

        result = self._trello.create_card(
            title=card_title,
            description=card_description,
            list_id=settings.TRELLO_LIST_ID or "default",
        )

        # Add checklist with suggested files
        if triage.suggested_files and result["card_id"] != "mock-card-abc123":
            self._trello.add_checklist(
                card_id=result["card_id"],
                name="Files to investigate",
                items=triage.suggested_files,
            )

        # Persist Ticket
        ticket_entity = Ticket(
            incident_id=incident.id,
            trello_card_id=result["card_id"],
            trello_card_url=result["card_url"],
            trello_list_id=settings.TRELLO_LIST_ID or "default",
            status="created",
        )
        self._db.add(ticket_entity)
        self._db.commit()

        duration_ms = int((time.monotonic() - start) * 1000)
        emit_event(
            "ticket", "success", triage.trace_id, duration_ms,
            incident_id=incident.id,
            metadata={
                "card_id": result["card_id"],
                "card_url": result["card_url"],
                "mock": settings.MOCK_INTEGRATIONS,
            },
        )

        return TicketDTO(
            incident_id=incident.id,
            trace_id=triage.trace_id,
            trello_card_id=result["card_id"],
            trello_card_url=result["card_url"],
            trello_list_id=settings.TRELLO_LIST_ID or "default",
        )
