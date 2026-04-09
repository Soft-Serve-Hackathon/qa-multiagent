"""Ticket Creation Use Case — thin wrapper; logic lives in TicketAgent."""
from sqlalchemy.orm import Session
from src.agents.ticket_agent import TicketAgent
from src.application.dto import TriageResultDTO, TicketDTO


class TicketCreationUseCase:
    def __init__(self, db: Session):
        self._db = db

    def execute(self, triage_dto: TriageResultDTO) -> TicketDTO:
        agent = TicketAgent(self._db)
        return agent.process(triage_dto)
