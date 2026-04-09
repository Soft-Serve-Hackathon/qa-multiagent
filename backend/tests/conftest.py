"""Pytest fixtures — shared mocks and in-memory test database."""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from src.domain.entities import Base
from src.infrastructure.database import get_db
from src.main import app

# StaticPool: all connections share the same in-memory SQLite instance
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
Base.metadata.create_all(bind=test_engine)  # Create tables once at import time


@pytest.fixture(autouse=True)
def setup_test_db():
    # Wipe and recreate tables before each test for isolation
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def mock_llm():
    with patch("src.agents.triage_agent.get_llm_client") as mock_factory:
        instance = MagicMock()
        instance.triage_incident.return_value = {
            "severity": "P2",
            "affected_module": "cart",
            "technical_summary": "Checkout fails due to CartService mutation error.",
            "suggested_files": ["packages/medusa/src/services/cart.ts"],
            "confidence_score": 0.87,
        }
        mock_factory.return_value = instance
        yield instance


@pytest.fixture
def mock_trello():
    with patch("src.agents.ticket_agent.TrelloClient") as MockClass:
        instance = MagicMock()
        instance.create_card.return_value = {
            "card_id": "test-card-123",
            "card_url": "https://trello.com/c/test-card-123",
        }
        instance.get_cards_in_list.return_value = []
        MockClass.return_value = instance
        yield instance


@pytest.fixture
def mock_slack():
    with patch("src.agents.notify_agent.SlackClient") as MockClass:
        instance = MagicMock()
        instance.post_incident_alert.return_value = True
        instance.post_resolution_notice.return_value = True
        MockClass.return_value = instance
        yield instance


@pytest.fixture
def mock_sendgrid():
    with patch("src.agents.notify_agent.SendGridClient") as MockClass:
        instance = MagicMock()
        instance.send_confirmation.return_value = True
        instance.send_resolution.return_value = True
        MockClass.return_value = instance
        yield instance
