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

        background_tasks.add_task(_run_pipeline, incident.id)

        return IncidentCreatedResponse(
            incident_id=incident.id,
            trace_id=incident.trace_id,
        )


def _run_pipeline(incident_id: int) -> None:
    """Background task: triage → qa_scope → fix_recommendation → ticket → notify."""
    from src.agents.triage_agent import TriageAgent
    from src.agents.qa_agent import QAAgent
    from src.agents.fix_recommendation_agent import FixRecommendationAgent
    from src.agents.ticket_agent import TicketAgent
    from src.agents.notify_agent import NotifyAgent

    db = SessionLocal()
    try:
        # Stage 1: Triage (LLM + Medusa repo context)
        triage_dto = TriageAgent(db).process(incident_id)

        # Stage 2: QA Scope — finds/proposes tests (continues on failure)
        qa_dto = QAAgent(db).process(triage_dto)

        # Stage 3: Fix Recommendation — proposes fix (continues on failure)
        fix_dto = FixRecommendationAgent(db).process(triage_dto, qa_dto)

        # Stage 4: Ticket — deduplication + Trello card with full context
        ticket_dto = TicketAgent(db).process(triage_dto, qa_dto, fix_dto)

        # Stage 5: Notify — skip if deduplicated (no new card was created)
        if not ticket_dto.deduplicated:
            NotifyAgent(db).process(triage_dto, ticket_dto, notification_type="team_and_reporter")

    except Exception:
        pass  # Errors are logged as observability events inside each agent
    finally:
        db.close()
