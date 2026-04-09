"""Notify Incident Use Case — thin wrapper; logic lives in NotifyAgent."""
from sqlalchemy.orm import Session
from src.agents.notify_agent import NotifyAgent
from src.application.dto import TriageResultDTO, TicketDTO


class NotifyIncidentUseCase:
    def __init__(self, db: Session):
        self._db = db

    def execute(self, triage_dto: TriageResultDTO, ticket_dto: TicketDTO, notification_type: str = "team_and_reporter") -> None:
        agent = NotifyAgent(self._db)
        agent.process(triage_dto, ticket_dto, notification_type)
