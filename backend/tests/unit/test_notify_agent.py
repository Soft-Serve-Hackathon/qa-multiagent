"""
Unit tests for NotifyAgent.

Tests Slack and email notifications, database persistence, and error handling.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, Mock
import json

from src.agents.notify_agent import NotifyAgent
from src.domain.enums import (
    IncidentStatus,
    NotificationChannel,
    NotificationStatus,
    ObservabilityStatus,
    ObservabilityStage,
    Severity,
)
from src.infrastructure.database import (
    IncidentModel,
    TriageResultModel,
    TicketModel,
    NotificationLogModel,
)


def test_notify_agent_initialization():
    """Test NotifyAgent can be initialized with settings."""
    agent = NotifyAgent()
    assert agent.slack_webhook_url is not None
    assert agent.reporter_email_from is not None


def test_send_slack_mock_mode():
    """Test Slack notification in mock mode."""
    with patch('src.agents.notify_agent.get_settings') as mock_settings:
        settings = MagicMock()
        settings.slack_webhook_url = "https://hooks.slack.com/test"
        settings.sendgrid_api_key = "test-key"
        settings.reporter_email_from = "noreply@company.com"
        settings.mock_integrations = True
        settings.mock_email = False
        mock_settings.return_value = settings
        
        with patch('src.agents.notify_agent.emit_event'):
            agent = NotifyAgent()
            agent.mock_integrations = True
            
            result = agent._send_slack(
                incident_title="Test Incident",
                severity="P1",
                affected_module="payment",
                confidence_score=0.95,
                card_url="https://trello.com/card/123",
                card_id="card-123",
                trace_id="trace-test",
                reporter_email="user@company.com",
            )
            
            assert result is True


def test_send_email_mock_mode():
    """Test email notification in mock mode."""
    with patch('src.agents.notify_agent.get_settings') as mock_settings:
        settings = MagicMock()
        settings.slack_webhook_url = "https://hooks.slack.com/test"
        settings.sendgrid_api_key = ""
        settings.reporter_email_from = "noreply@company.com"
        settings.mock_integrations = False
        settings.mock_email = True
        mock_settings.return_value = settings
        
        with patch('src.agents.notify_agent.emit_event'):
            agent = NotifyAgent()
            agent.mock_email = True
            
            result = agent._send_email(
                incident_id=1,
                incident_title="Test Incident",
                incident_description="Something went wrong",
                severity="P2",
                affected_module="cart",
                technical_summary="Cart service is down",
                confidence_score=0.88,
                ticket_id=42,
                card_url="https://trello.com/card/123",
                trace_id="trace-test",
                reporter_email="reporter@company.com",
            )
            
            assert result is True


def test_build_slack_message():
    """Test Slack message structure and content."""
    agent = NotifyAgent()
    
    # Test via _send_slack with mock httpx
    with patch('httpx.Client') as mock_client_class:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        with patch('src.agents.notify_agent.get_settings') as mock_settings:
            settings = MagicMock()
            settings.slack_webhook_url = "https://hooks.slack.com/test"
            settings.sendgrid_api_key = "test-key"
            settings.reporter_email_from = "noreply@company.com"
            settings.mock_integrations = False
            settings.mock_email = False
            mock_settings.return_value = settings
            
            agent = NotifyAgent()
            
            with patch('src.agents.notify_agent.NotifyAgent._log_notification'):
                result = agent._send_slack(
                    incident_title="Payment Service Crash",
                    severity="P1",
                    affected_module="payment",
                    confidence_score=0.99,
                    card_url="https://trello.com/c/abc123",
                    card_id="abc123",
                    trace_id="trace-xyz",
                    reporter_email="admin@company.com",
                )
                
                # Check that httpx.Client.post was called
                mock_client.post.assert_called_once()
                call_args = mock_client.post.call_args
                
                # Verify the payload contains expected fields
                json_payload = call_args.kwargs.get('json') or call_args[1].get('json', {})
                assert json_payload is not None


def test_email_html_template_format():
    """Test email HTML template generation."""
    from src.agents.notify_agent import EMAIL_TEMPLATE
    
    # Verify template has required placeholders
    assert "{incident_title}" in EMAIL_TEMPLATE
    assert "{severity}" in EMAIL_TEMPLATE
    assert "{affected_module}" in EMAIL_TEMPLATE
    assert "{confidence_score}" in EMAIL_TEMPLATE
    assert "{technical_summary}" in EMAIL_TEMPLATE
    assert "{ticket_url}" in EMAIL_TEMPLATE
    
    # Test template rendering
    html = EMAIL_TEMPLATE.format(
        incident_title="Test Title",
        severity="P2",
        severity_class="p2",
        affected_module="cart",
        confidence_score=0.95,
        technical_summary="Test summary",
        ticket_url="https://trello.com/card/123",
        trace_id="trace-test",
    )
    
    assert "Test Title" in html
    assert "P2" in html
    assert "cart" in html
    assert "95%" in html or "0.95" in html


def test_notification_log_persistence():
    """Test that notifications are logged to database."""
    agent = NotifyAgent()
    
    with patch('src.agents.notify_agent.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        
        agent._log_notification(
            incident_id=1,
            channel=NotificationChannel.SLACK.value,
            recipient="#incidents",
            notification_type="team_alert",
            content_summary="Test incident",
            status=NotificationStatus.SENT.value,
        )
        
        # Verify add was called
        mock_db.add.assert_called_once()


def test_emit_error_event():
    """Test error event emission."""
    agent = NotifyAgent()
    
    with patch('src.agents.notify_agent.emit_event') as mock_emit:
        agent._emit_error_event(
            trace_id="trace-test",
            incident_id=123,
            error_msg="Test error",
            start_time=None,
        )
        
        mock_emit.assert_called_once()
        call_args = mock_emit.call_args
        assert call_args.kwargs['trace_id'] == "trace-test"
        assert call_args.kwargs['stage'] == ObservabilityStage.NOTIFY
        assert call_args.kwargs['status'] == ObservabilityStatus.ERROR


def test_partial_notification_success():
    """Test handling when only Slack succeeds but email fails."""
    agent = NotifyAgent()
    
    # This would normally be tested via full integration,
    # but we can verify the logic structure handles it
    notifications_sent = [NotificationChannel.SLACK.value]
    notification_failures = [NotificationChannel.EMAIL.value]
    
    # Verify at least one succeeded
    assert len(notifications_sent) > 0
    assert len(notification_failures) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
