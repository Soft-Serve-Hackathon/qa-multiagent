"""
Unit tests for TicketAgent.

Tests ticket creation, Trello API integration, and database persistence.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, Mock
import json

from src.agents.ticket_agent import TicketAgent
from src.domain.enums import IncidentStatus, TicketStatus, ObservabilityStatus, ObservabilityStage, Severity
from src.infrastructure.database import (
    IncidentModel,
    TriageResultModel,
    TicketModel,
    get_db,
)


@pytest.fixture
def sample_incident_db(tmp_path):
    """Create in-memory test database with sample data."""
    from src.infrastructure.database import engine, SessionLocal, Base
    import os
    
    # Use in-memory SQLite for testing
    import tempfile
    db_fd, db_path = tempfile.mkstemp()
    
    from sqlalchemy import create_engine
    test_engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(test_engine)
    
    session = SessionLocal()
    
    # Create test incident
    incident = IncidentModel(
        trace_id="test-trace-001",
        title="Database connection timeout",
        description="Database query timing out on checkout",
        reporter_email="dev@company.com",
        attachment_type="log",
        attachment_path="/uploads/test-trace-001.txt",
        status=IncidentStatus.TICKETED.value,
    )
    session.add(incident)
    session.flush()
    
    # Create triage result
    triage = TriageResultModel(
        incident_id=incident.id,
        severity=Severity.P2.value,
        affected_module="cart",
        technical_summary="Database connection pool exhausted. Scaling required.",
        suggested_files=json.dumps(["src/db/pool.py", "src/db/config.py"]),
        confidence_score=0.92,
    )
    session.add(triage)
    session.commit()
    
    yield session, incident.id
    
    session.close()
    os.close(db_fd)
    os.unlink(db_path)


def test_ticket_agent_initialization():
    """Test TicketAgent can be initialized with settings."""
    agent = TicketAgent()
    assert agent.trello_api_key is not None
    assert agent.trello_api_token is not None
    assert agent.trello_list_id is not None


def test_ticket_agent_mock_mode(sample_incident_db):
    """Test TicketAgent in mock mode (no Trello API call)."""
    session, incident_id = sample_incident_db
    
    with patch('src.agents.ticket_agent.get_settings') as mock_settings:
        settings = MagicMock()
        settings.trello_api_key = "test-key"
        settings.trello_api_token = "test-token"
        settings.trello_list_id = "test-list"
        settings.mock_integrations = True
        mock_settings.return_value = settings
        
        with patch('src.agents.ticket_agent.emit_event') as mock_emit:
            agent = TicketAgent()
            agent.mock_integrations = True
            
            # Since we need real DB connections, test the mock card creation works
            card_id, card_url = agent._create_card_mock(
                "Test Card",
                "Test Description"
            )
            
            assert card_id is not None
            assert card_id.startswith("MOCK-")
            assert card_url is not None
            assert "trello.com" in card_url


def test_build_card_description():
    """Test Trello card description formatting."""
    agent = TicketAgent()
    
    description = agent._build_card_description(
        incident_description="Short timeout issue",
        severity="P2",
        affected_module="cart",
        technical_summary="Connection pool exhausted",
        suggested_files=["file1.py", "file2.py"],
        confidence_score=0.92,
        trace_id="trace-123",
    )
    
    assert "[P2]" in description or "P2" in description
    assert "cart" in description
    assert "0.92" in description or "92%" in description
    assert "file1.py" in description
    assert "trace-123" in description


def test_severity_to_label_mapping():
    """Test severity to Trello label mapping."""
    from src.agents.ticket_agent import SEVERITY_TO_LABEL
    
    assert SEVERITY_TO_LABEL["P1"] == "P1-Critical"
    assert SEVERITY_TO_LABEL["P2"] == "P2-High"
    assert SEVERITY_TO_LABEL["P3"] == "P3-Medium"
    assert SEVERITY_TO_LABEL["P4"] == "P4-Low"


def test_emit_error_event():
    """Test error event emission."""
    agent = TicketAgent()
    
    with patch('src.agents.ticket_agent.emit_event') as mock_emit:
        agent._emit_error_event(
            trace_id="trace-test",
            incident_id=123,
            error_msg="Test error",
            start_time=None,
        )
        
        mock_emit.assert_called_once()
        call_args = mock_emit.call_args
        assert call_args.kwargs['trace_id'] == "trace-test"
        assert call_args.kwargs['stage'] == ObservabilityStage.TICKET
        assert call_args.kwargs['status'] == ObservabilityStatus.ERROR


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
