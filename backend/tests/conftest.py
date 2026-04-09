"""Pytest configuration and fixtures."""
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_llm_client():
    """Mock Anthropic Claude API client."""
    with patch('src.infrastructure.llm.client.AnthropicClient') as mock:
        yield mock()


@pytest.fixture
def mock_trello_client():
    """Mock Trello API client."""
    with patch('src.infrastructure.external.trello_client.TrelloClient') as mock:
        yield mock()


@pytest.fixture
def mock_slack_client():
    """Mock Slack webhook client."""
    with patch('src.infrastructure.external.slack_client.SlackClient') as mock:
        yield mock()


@pytest.fixture
def mock_sendgrid_client():
    """Mock SendGrid email client."""
    with patch('src.infrastructure.external.sendgrid_client.SendGridClient') as mock:
        yield mock()
