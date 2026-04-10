"""TicketAgent — deduplicates, then creates a Trello card enriched with QA + fix context."""
import time
import json
import threading
from difflib import SequenceMatcher
from sqlalchemy.orm import Session

from src.domain.entities import Incident, Ticket
from src.application.dto import TriageResultDTO, QAScopeDTO, FixRecommendationDTO, TicketDTO
from src.infrastructure.external.trello_client import TrelloClient
from src.infrastructure.routing.owner_router import resolve_owner
from src.infrastructure.observability.events import emit_event
from src.config import settings

DEDUP_THRESHOLD = 0.75
DEDUP_LOOKBACK = 20

# Serializes dedup-check + ticket-insert across concurrent pipeline threads.
# Without this lock, two incidents arriving simultaneously both pass the dedup
# check before either commits its ticket → duplicate cards in Trello.
_dedup_lock = threading.Lock()


class TicketDeduplicator:
    """
    Checks whether a near-identical ticket already exists for the same module.
    Uses weighted string similarity: 60% title + 40% description (first 200 chars).
    """

    def __init__(self, db: Session):
        self._db = db

    def find_similar_ticket(
        self,
        incident_title: str,
        incident_description: str,
        affected_module: str,
        threshold: float = DEDUP_THRESHOLD,
    ) -> tuple[Ticket, float] | None:
        """Return (ticket, score) if a duplicate is found, else None."""
        recent = (
            self._db.query(Ticket)
            .join(Incident, Ticket.incident_id == Incident.id)
            .filter(
                Ticket.status == "created",
                Incident.status.notin_(["deduplicated", "error"]),
            )
            .order_by(Ticket.created_at.desc())
            .limit(DEDUP_LOOKBACK)
            .all()
        )

        best_ticket, best_score = None, 0.0
        for ticket in recent:
            existing_incident = self._db.query(Incident).filter(Incident.id == ticket.incident_id).first()
            if not existing_incident:
                continue

            title_sim = self._string_similarity(incident_title, existing_incident.title)
            desc_sim = self._string_similarity(
                incident_description[:200], existing_incident.description[:200]
            )
            score = (title_sim * 0.6) + (desc_sim * 0.4)

            if score > best_score:
                best_score = score
                best_ticket = ticket

        if best_score >= threshold and best_ticket:
            return best_ticket, best_score
        return None

    @staticmethod
    def _string_similarity(a: str, b: str) -> float:
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()


class TicketAgent:
    """
    Responsibility: Check for duplicates, then build the Trello card payload enriched
    with QA and fix context. Persists Ticket entity. Updates Incident status.
    """

    def __init__(self, db: Session):
        self._db = db
        self._trello = TrelloClient()

    def process(
        self,
        triage: TriageResultDTO,
        qa: QAScopeDTO | None = None,
        fix: FixRecommendationDTO | None = None,
    ) -> TicketDTO:
        start = time.monotonic()
        incident: Incident = self._db.query(Incident).filter(Incident.id == triage.incident_id).first()

        # ── Deduplication check + ticket creation (atomic under lock) ──────────
        # Lock prevents race condition: two simultaneous pipelines both passing
        # the dedup check before either commits its ticket to the database.
        with _dedup_lock:
            deduplicator = TicketDeduplicator(self._db)
            dedup_result = deduplicator.find_similar_ticket(
                incident_title=incident.title,
                incident_description=incident.description,
                affected_module=triage.affected_module,
            )

            if dedup_result:
                existing_ticket, similarity_score = dedup_result
                incident.status = "deduplicated"
                incident.linked_ticket_id = existing_ticket.id
                self._db.commit()

                duration_ms = int((time.monotonic() - start) * 1000)
                emit_event(
                    "ticket", "deduplicated", triage.trace_id, duration_ms,
                    incident_id=incident.id,
                    metadata={
                        "linked_ticket_id": existing_ticket.id,
                        "linked_card_id": existing_ticket.trello_card_id,
                        "linked_card_url": existing_ticket.trello_card_url or "",
                        "similarity_score": round(similarity_score, 3),
                        "threshold": DEDUP_THRESHOLD,
                    },
                )

                return TicketDTO(
                    incident_id=incident.id,
                    trace_id=triage.trace_id,
                    trello_card_id=existing_ticket.trello_card_id or "",
                    trello_card_url=existing_ticket.trello_card_url or "",
                    trello_list_id=existing_ticket.trello_list_id,
                    deduplicated=True,
                    linked_ticket_id=existing_ticket.id,
                )

            # ── Commit a placeholder ticket row BEFORE releasing the lock ─────
            # This ensures the next thread sees this incident as "taken" when it
            # runs its own dedup check, even before the Trello API call completes.
            ticket_entity = Ticket(
                incident_id=incident.id,
                trello_card_id="pending",
                trello_card_url="",
                trello_list_id=settings.TRELLO_LIST_ID or "default",
                status="created",
            )
            self._db.add(ticket_entity)
            incident.status = "ticketed"
            self._db.commit()
            self._db.refresh(ticket_entity)
        # lock released — Trello API call happens outside the lock (slow I/O)

        # ── Build card description ────────────────────────────────────────────
        files_list = "\n".join(f"- {f}" for f in triage.suggested_files) or "- No specific files identified"

        card_description = (
            f"## Technical Summary\n{triage.technical_summary}\n\n"
            f"## Affected Module\n`{triage.affected_module}` (confidence: {int(triage.confidence_score * 100)}%)\n\n"
            f"## Suggested Files to Investigate\n{files_list}\n\n"
        )

        if qa and not qa.qa_incomplete:
            reproduced_str = "✅ Yes" if qa.reproduced else "❌ Not reproduced automatically"
            card_description += f"## QA Scope\n**Reproduced:** {reproduced_str}\n"
            if qa.test_evidence_summary:
                card_description += f"**Evidence:** {qa.test_evidence_summary}\n"
            if qa.failing_tests:
                card_description += f"**Failing tests:**\n" + "\n".join(f"- `{t}`" for t in qa.failing_tests) + "\n"
            if qa.new_tests_created:
                card_description += f"**Proposed regression test:**\n```typescript\n{qa.new_tests_created[0]}\n```\n"
            card_description += "\n"
        elif qa and qa.qa_incomplete:
            card_description += "## QA Scope\n⚠️ QA analysis incomplete — manual review required.\n\n"

        if fix and not fix.fix_incomplete:
            risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(fix.risk_level, "⚪")
            card_description += (
                f"## Fix Recommendation\n{fix.proposed_fix_summary}\n"
                f"**Risk level:** {risk_emoji} {fix.risk_level.upper()}\n"
            )
            if fix.post_fix_test_result:
                card_description += f"**Validation:** {fix.post_fix_test_result}\n"
            card_description += "\n"
        elif fix and fix.fix_incomplete:
            card_description += "## Fix Recommendation\n⚠️ Fix analysis incomplete — manual assessment required.\n\n"

        card_description += (
            f"## Reporter\n{incident.reporter_email}\n\n"
            f"## Trace ID\n`{triage.trace_id}`"
        )

        card_title = f"[{triage.severity}] {incident.title}"

        result = self._trello.create_card(
            title=card_title,
            description=card_description,
            list_id=settings.TRELLO_LIST_ID or "default",
        )

        owner = resolve_owner(triage.affected_module)
        assigned_trello_member_id = owner.get("trello_member_id")
        assigned_slack_user_id = owner.get("slack_user_id")

        assignment_ok = False
        if assigned_trello_member_id:
            assignment_ok = self._trello.assign_member(result["card_id"], assigned_trello_member_id)

        if triage.suggested_files and result["card_id"] != "mock-card-abc123":
            self._trello.add_checklist(
                card_id=result["card_id"],
                name="Files to investigate",
                items=triage.suggested_files,
            )

        # Update the placeholder row with the real Trello card data
        ticket_entity.trello_card_id = result["card_id"]
        ticket_entity.trello_card_url = result["card_url"]
        self._db.commit()

        duration_ms = int((time.monotonic() - start) * 1000)
        emit_event(
            "ticket", "success", triage.trace_id, duration_ms,
            incident_id=incident.id,
            metadata={
                "card_id": result["card_id"],
                "card_url": result["card_url"],
                "assigned_trello_member_id": assigned_trello_member_id,
                "assigned_slack_user_id": assigned_slack_user_id,
                "assignment_ok": assignment_ok,
                "qa_included": qa is not None and not qa.qa_incomplete,
                "fix_included": fix is not None and not fix.fix_incomplete,
                "mock": settings.MOCK_INTEGRATIONS,
            },
        )

        return TicketDTO(
            incident_id=incident.id,
            trace_id=triage.trace_id,
            trello_card_id=result["card_id"],
            trello_card_url=result["card_url"],
            trello_list_id=settings.TRELLO_LIST_ID or "default",
            assigned_trello_member_id=assigned_trello_member_id,
            assigned_slack_user_id=assigned_slack_user_id,
            deduplicated=False,
        )
