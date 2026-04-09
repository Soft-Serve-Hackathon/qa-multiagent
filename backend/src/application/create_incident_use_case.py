"""Create Incident Use Case — validates input, persists, then kicks off background pipeline."""
from typing import Optional
from fastapi import UploadFile, BackgroundTasks
from sqlalchemy.orm import Session

from src.api.models import IncidentCreatedResponse
from src.agents.ingest_agent import IngestAgent
from src.infrastructure.database import SessionLocal


class CreateIncidentUseCase:
    def __init__(self, db: Session):
        self._db = db

    async def execute(
        self,
        title: str,
        description: str,
        reporter_email: str,
        attachment: Optional[UploadFile],
        background_tasks: BackgroundTasks,
    ) -> IncidentCreatedResponse:
        agent = IngestAgent(self._db)
        incident = await agent.process(
            title=title,
            description=description,
            reporter_email=reporter_email,
            attachment=attachment,
        )

        # Kick off the rest of the pipeline in background (non-blocking)
        background_tasks.add_task(_run_pipeline, incident.id)

        return IncidentCreatedResponse(
            incident_id=incident.id,
            trace_id=incident.trace_id,
        )


def _run_pipeline(incident_id: int) -> None:
    """Background task: triage → ticket → notify. Each step updates the DB."""
    from src.agents.triage_agent import TriageAgent
    from src.agents.ticket_agent import TicketAgent
    from src.agents.notify_agent import NotifyAgent

    db = SessionLocal()
    try:
        triage_agent = TriageAgent(db)
        triage_dto = triage_agent.process(incident_id)

        ticket_agent = TicketAgent(db)
        ticket_dto = ticket_agent.process(triage_dto)

        notify_agent = NotifyAgent(db)
        notify_agent.process(triage_dto, ticket_dto, notification_type="team_and_reporter")
    except Exception:
        pass  # Errors are logged inside each agent
    finally:
        db.close()
