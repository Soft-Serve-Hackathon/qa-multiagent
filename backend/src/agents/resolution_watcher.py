"""ResolutionWatcher — background thread that polls Trello for resolved cards."""
import threading
import time
from src.config import settings
from src.infrastructure.database import SessionLocal
from src.infrastructure.external.trello_client import TrelloClient
from src.domain.entities import Incident, Ticket


class ResolutionWatcher:
    """
    Responsibility: Poll Trello's Done list periodically.
    When a card is found there, mark the incident as resolved and notify the reporter.
    Runs as a daemon thread — started by FastAPI lifespan.
    """

    def __init__(self):
        self._trello = TrelloClient()
        self._interval = settings.RESOLUTION_WATCHER_INTERVAL_SECONDS
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="ResolutionWatcher")
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._check_resolutions()
            except Exception:
                pass  # Errors logged inside _check_resolutions
            self._stop_event.wait(self._interval)

    def _check_resolutions(self) -> None:
        done_list_id = settings.TRELLO_DONE_LIST_ID
        if not done_list_id or settings.MOCK_INTEGRATIONS:
            return

        done_cards = self._trello.get_cards_in_list(done_list_id)
        if not done_cards:
            return

        done_card_ids = {card["id"] for card in done_cards}

        db = SessionLocal()
        try:
            # Find tickets in DB that are in the Done list but incident not yet resolved
            tickets = (
                db.query(Ticket)
                .filter(Ticket.trello_card_id.in_(done_card_ids), Ticket.resolved_at.is_(None))
                .all()
            )
            for ticket in tickets:
                incident = db.query(Incident).filter(Incident.id == ticket.incident_id).first()
                if incident and incident.status != "resolved":
                    from src.agents.notify_agent import NotifyAgent
                    notify_agent = NotifyAgent(db)
                    notify_agent.send_resolution(incident, ticket)
                    ticket.resolved_at = __import__("datetime").datetime.utcnow()
                    db.commit()
        finally:
            db.close()


# Singleton instance
_watcher: ResolutionWatcher | None = None


def get_watcher() -> ResolutionWatcher:
    global _watcher
    if _watcher is None:
        _watcher = ResolutionWatcher()
    return _watcher
