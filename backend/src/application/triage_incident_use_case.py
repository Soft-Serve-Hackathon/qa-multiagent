"""Triage Incident Use Case — thin wrapper kept for symmetry; logic lives in TriageAgent."""
from sqlalchemy.orm import Session
from src.agents.triage_agent import TriageAgent
from src.application.dto import TriageResultDTO


class TriageIncidentUseCase:
    def __init__(self, db: Session):
        self._db = db

    def execute(self, incident_id: int) -> TriageResultDTO:
        agent = TriageAgent(self._db)
        return agent.process(incident_id)
