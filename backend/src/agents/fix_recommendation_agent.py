"""FixRecommendationAgent — proposes a technical fix based on triage + QA evidence. Stage: fix_recommendation."""
import json
import time
from sqlalchemy.orm import Session

from src.domain.entities import Incident, FixRecommendationResult
from src.application.dto import TriageResultDTO, QAScopeDTO, FixRecommendationDTO
from src.infrastructure.llm.client import get_llm_client
from src.infrastructure.observability.events import emit_event


class FixRecommendationAgent:
    """
    Responsibility: Given triage + QA scope results, inspect the affected source files
    and propose a concrete technical fix with risk assessment.

    Inserted between QAAgent and TicketAgent in the pipeline.
    If this agent fails, the pipeline continues with fix_incomplete=True.
    """

    def __init__(self, db: Session):
        self._db = db
        self._llm = get_llm_client()

    def process(self, triage: TriageResultDTO, qa: QAScopeDTO) -> FixRecommendationDTO:
        start = time.monotonic()
        incident: Incident = self._db.query(Incident).filter(Incident.id == triage.incident_id).first()

        try:
            raw_result = self._llm.fix_recommendation_incident(
                triage={
                    "severity": triage.severity,
                    "affected_module": triage.affected_module,
                    "technical_summary": triage.technical_summary,
                    "suggested_files": triage.suggested_files,
                },
                qa={
                    "reproduced": qa.reproduced,
                    "failing_tests": qa.failing_tests,
                    "test_evidence_summary": qa.test_evidence_summary,
                },
            )

            fix_entity = FixRecommendationResult(
                incident_id=incident.id,
                proposed_fix_summary=raw_result.get("proposed_fix_summary", ""),
                proposed_files=json.dumps(raw_result.get("proposed_files", [])),
                risk_level=raw_result.get("risk_level", "medium"),
                post_fix_test_result=raw_result.get("post_fix_test_result", ""),
                fix_incomplete=False,
                raw_llm_response=json.dumps(raw_result),
            )
            self._db.add(fix_entity)
            self._db.commit()

            duration_ms = int((time.monotonic() - start) * 1000)
            emit_event(
                "fix_recommendation", "success", incident.trace_id, duration_ms,
                incident_id=incident.id,
                metadata={
                    "risk_level": raw_result.get("risk_level", "medium"),
                    "proposed_files_count": len(raw_result.get("proposed_files", [])),
                    "module": triage.affected_module,
                },
            )

            return FixRecommendationDTO(
                incident_id=incident.id,
                trace_id=incident.trace_id,
                proposed_fix_summary=raw_result.get("proposed_fix_summary", ""),
                proposed_files=raw_result.get("proposed_files", []),
                risk_level=raw_result.get("risk_level", "medium"),
                post_fix_test_result=raw_result.get("post_fix_test_result", ""),
                fix_incomplete=False,
            )

        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            emit_event(
                "fix_recommendation", "skipped", incident.trace_id, duration_ms,
                incident_id=incident.id,
                metadata={"error": str(exc)[:200], "fix_incomplete": True},
            )
            return FixRecommendationDTO(
                incident_id=incident.id,
                trace_id=incident.trace_id,
                fix_incomplete=True,
            )
