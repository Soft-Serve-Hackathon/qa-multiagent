"""QAAgent — finds/proposes tests for the affected module. Stage: qa_scope."""
import json
import time
from sqlalchemy.orm import Session

from src.domain.entities import Incident, QAScopeResult
from src.application.dto import TriageResultDTO, QAScopeDTO
from src.infrastructure.llm.client import get_llm_client
from src.infrastructure.observability.events import emit_event


class QAAgent:
    """
    Responsibility: Given triage output, inspect the Medusa.js test suite for the
    affected module and assess test coverage. If coverage is missing, propose a
    minimal regression test snippet.

    Inserted between TriageAgent and FixRecommendationAgent in the pipeline.
    If this agent fails, the pipeline continues with qa_incomplete=True.
    """

    def __init__(self, db: Session):
        self._db = db
        self._llm = get_llm_client()

    def process(self, triage: TriageResultDTO) -> QAScopeDTO:
        start = time.monotonic()
        incident: Incident = self._db.query(Incident).filter(Incident.id == triage.incident_id).first()

        try:
            raw_result = self._llm.qa_scope_incident({
                "severity": triage.severity,
                "affected_module": triage.affected_module,
                "technical_summary": triage.technical_summary,
                "suggested_files": triage.suggested_files,
            })

            qa_entity = QAScopeResult(
                incident_id=incident.id,
                reproduced=raw_result.get("reproduced", False),
                failing_tests=json.dumps(raw_result.get("failing_tests", [])),
                new_tests_created=json.dumps(raw_result.get("new_tests_created", [])),
                test_evidence_summary=raw_result.get("test_evidence_summary", ""),
                coverage_files=json.dumps(raw_result.get("coverage_files", [])),
                qa_incomplete=False,
                raw_llm_response=json.dumps(raw_result),
            )
            self._db.add(qa_entity)
            self._db.commit()

            duration_ms = int((time.monotonic() - start) * 1000)
            emit_event(
                "qa_scope", "success", incident.trace_id, duration_ms,
                incident_id=incident.id,
                metadata={
                    "reproduced": raw_result.get("reproduced", False),
                    "failing_tests_count": len(raw_result.get("failing_tests", [])),
                    "new_tests_count": len(raw_result.get("new_tests_created", [])),
                    "coverage_files_found": len(raw_result.get("coverage_files", [])),
                    "module": triage.affected_module,
                },
            )

            return QAScopeDTO(
                incident_id=incident.id,
                trace_id=incident.trace_id,
                reproduced=raw_result.get("reproduced", False),
                failing_tests=raw_result.get("failing_tests", []),
                new_tests_created=raw_result.get("new_tests_created", []),
                test_evidence_summary=raw_result.get("test_evidence_summary", ""),
                coverage_files=raw_result.get("coverage_files", []),
                qa_incomplete=False,
            )

        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            emit_event(
                "qa_scope", "skipped", incident.trace_id, duration_ms,
                incident_id=incident.id,
                metadata={"error": str(exc)[:200], "qa_incomplete": True},
            )
            # Do NOT persist a failed entity — return a stub DTO so the pipeline continues
            return QAScopeDTO(
                incident_id=incident.id,
                trace_id=incident.trace_id,
                qa_incomplete=True,
            )
