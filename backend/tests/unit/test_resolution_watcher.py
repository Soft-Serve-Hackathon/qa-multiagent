"""
Unit tests for ResolutionWatcher.

Tests async start/stop, polling loop, Trello card detection, and resolution notifications.
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, AsyncMock
import json

from src.agents.resolution_watcher import ResolutionWatcher
from src.domain.enums import (
    IncidentStatus,
    NotificationChannel,
    NotificationStatus,
    ObservabilityStatus,
    ObservabilityStage,
)
from src.infrastructure.database import (
    IncidentModel,
    TicketModel,
    NotificationLogModel,
)


@pytest.mark.asyncio
async def test_resolution_watcher_initialization():
    """Test ResolutionWatcher initializes with correct settings."""
    watcher = ResolutionWatcher()
    assert watcher.trello_api_key is not None
    assert watcher.poll_interval == 60
    assert watcher.notify_agent is not None


@pytest.mark.asyncio
async def test_resolution_watcher_start_stop():
    """Test async start and stop gracefully."""
    watcher = ResolutionWatcher()

    # Start watcher
    await watcher.start()
    assert watcher._stop_event is not None
    assert watcher._polling_task is not None

    # Give it a moment to initialize
    await asyncio.sleep(0.1)

    # Stop watcher
    await watcher.stop()

    # Task should be completed
    assert watcher._polling_task.done()


@pytest.mark.asyncio
async def test_resolution_watcher_stop_without_start():
    """Test stop handles gracefully when not started."""
    watcher = ResolutionWatcher()
    # Should not raise
    await watcher.stop()


@pytest.mark.asyncio
async def test_get_unresolved_tickets_empty():
    """Test getting unresolved tickets when none exist."""
    with patch('src.agents.resolution_watcher.get_db'):
        watcher = ResolutionWatcher()
        tickets = watcher._get_unresolved_tickets()
        assert isinstance(tickets, list)


@pytest.mark.asyncio
async def test_is_card_done_mock_mode():
    """Test card check in mock mode returns False."""
    with patch('src.agents.resolution_watcher.get_settings') as mock_settings:
        settings = MagicMock()
        settings.trello_api_key = "test-key"
        settings.trello_api_token = "test-token"
        settings.trello_done_list_id = "DONE-123"
        settings.resolution_watcher_interval_seconds = 60
        settings.mock_integrations = True
        mock_settings.return_value = settings

        with patch('src.agents.resolution_watcher.NotifyAgent'):
            watcher = ResolutionWatcher()
            result = await watcher._is_card_done("card-123", "trace-456")
            assert result is False


@pytest.mark.asyncio
async def test_is_card_done_not_configured():
    """Test card check when Trello not configured."""
    with patch('src.agents.resolution_watcher.get_settings') as mock_settings:
        settings = MagicMock()
        settings.trello_api_key = ""
        settings.trello_api_token = ""
        settings.trello_done_list_id = "DONE"
        settings.resolution_watcher_interval_seconds = 60
        settings.mock_integrations = False
        mock_settings.return_value = settings

        with patch('src.agents.resolution_watcher.NotifyAgent'):
            watcher = ResolutionWatcher()
            result = await watcher._is_card_done("card-123", "trace-456")
            assert result is False


@pytest.mark.asyncio
async def test_is_card_done_success():
    """Test card check successfully detects Done status."""
    with patch('src.agents.resolution_watcher.get_settings') as mock_settings:
        settings = MagicMock()
        settings.trello_api_key = "test-key"
        settings.trello_api_token = "test-token"
        settings.trello_done_list_id = "DONE-123"
        settings.resolution_watcher_interval_seconds = 60
        settings.mock_integrations = False
        mock_settings.return_value = settings

        with patch('src.agents.resolution_watcher.NotifyAgent'):
            with patch('src.agents.resolution_watcher.httpx.Client') as mock_client:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"idList": "DONE-123"}
                mock_client.return_value.__enter__.return_value.get.return_value = (
                    mock_response
                )

                watcher = ResolutionWatcher()
                result = await watcher._is_card_done("card-123", "trace-456")
                assert result is True


@pytest.mark.asyncio
async def test_is_card_done_not_done():
    """Test card check detects non-Done status."""
    with patch('src.agents.resolution_watcher.get_settings') as mock_settings:
        settings = MagicMock()
        settings.trello_api_key = "test-key"
        settings.trello_api_token = "test-token"
        settings.trello_done_list_id = "DONE-123"
        settings.resolution_watcher_interval_seconds = 60
        settings.mock_integrations = False
        mock_settings.return_value = settings

        with patch('src.agents.resolution_watcher.NotifyAgent'):
            with patch('src.agents.resolution_watcher.httpx.Client') as mock_client:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"idList": "TODO-456"}
                mock_client.return_value.__enter__.return_value.get.return_value = (
                    mock_response
                )

                watcher = ResolutionWatcher()
                result = await watcher._is_card_done("card-123", "trace-456")
                assert result is False


@pytest.mark.asyncio
async def test_is_card_done_api_error():
    """Test card check handles API errors gracefully."""
    with patch('src.agents.resolution_watcher.get_settings') as mock_settings:
        settings = MagicMock()
        settings.trello_api_key = "test-key"
        settings.trello_api_token = "test-token"
        settings.trello_done_list_id = "DONE"
        settings.resolution_watcher_interval_seconds = 60
        settings.mock_integrations = False
        mock_settings.return_value = settings

        with patch('src.agents.resolution_watcher.NotifyAgent'):
            with patch('src.agents.resolution_watcher.httpx.Client') as mock_client:
                mock_client.return_value.__enter__.return_value.get.side_effect = (
                    Exception("Network error")
                )

                watcher = ResolutionWatcher()
                result = await watcher._is_card_done("card-123", "trace-456")
                assert result is False


@pytest.mark.asyncio
async def test_send_resolution_notification_success():
    """Test sending resolution notification."""
    with patch('src.agents.resolution_watcher.get_settings') as mock_settings:
        settings = MagicMock()
        settings.trello_api_key = "test-key"
        settings.trello_api_token = "test-token"
        settings.trello_done_list_id = "DONE"
        settings.resolution_watcher_interval_seconds = 60
        settings.mock_integrations = False
        mock_settings.return_value = settings

        with patch('src.agents.resolution_watcher.NotifyAgent') as mock_notify:
            mock_notify_instance = MagicMock()
            mock_notify_instance.send_resolution_email.return_value = {
                "status": "sent"
            }
            mock_notify.return_value = mock_notify_instance

            watcher = ResolutionWatcher()

            ticket = MagicMock()
            ticket.incident_id = 1
            ticket.trello_card_url = "https://trello.com/c/abc123"

            result = await watcher._send_resolution_notification(
                "trace-123", ticket, "reporter@example.com"
            )

            assert result == "sent"
            mock_notify_instance.send_resolution_email.assert_called_once()


@pytest.mark.asyncio
async def test_send_resolution_notification_failed():
    """Test handling of failed resolution notification."""
    with patch('src.agents.resolution_watcher.get_settings') as mock_settings:
        settings = MagicMock()
        settings.trello_api_key = "test-key"
        settings.trello_api_token = "test-token"
        settings.trello_done_list_id = "DONE"
        settings.resolution_watcher_interval_seconds = 60
        settings.mock_integrations = False
        mock_settings.return_value = settings

        with patch('src.agents.resolution_watcher.NotifyAgent') as mock_notify:
            mock_notify_instance = MagicMock()
            mock_notify_instance.send_resolution_email.return_value = {
                "status": "failed",
                "error": "SendGrid error",
            }
            mock_notify.return_value = mock_notify_instance

            watcher = ResolutionWatcher()

            ticket = MagicMock()
            ticket.incident_id = 1
            ticket.trello_card_url = "https://trello.com/c/abc123"

            result = await watcher._send_resolution_notification(
                "trace-123", ticket, "reporter@example.com"
            )

            assert result == "failed"


@pytest.mark.asyncio
async def test_poll_once_no_tickets():
    """Test polling iteration with no unresolved tickets."""
    with patch('src.agents.resolution_watcher.get_settings') as mock_settings:
        settings = MagicMock()
        settings.trello_api_key = "test-key"
        settings.trello_api_token = "test-token"
        settings.trello_done_list_id = "DONE"
        settings.resolution_watcher_interval_seconds = 60
        settings.mock_integrations = True
        mock_settings.return_value = settings

        with patch('src.agents.resolution_watcher.NotifyAgent'):
            watcher = ResolutionWatcher()

            with patch.object(
                watcher, "_get_unresolved_tickets", return_value=[]
            ):
                # Should not raise
                await watcher._poll_once()


@pytest.mark.asyncio
async def test_polling_loop_respects_stop_event():
    """Test polling loop stops when stop event is set."""
    with patch('src.agents.resolution_watcher.get_settings') as mock_settings:
        settings = MagicMock()
        settings.trello_api_key = "test-key"
        settings.trello_api_token = "test-token"
        settings.trello_done_list_id = "DONE"
        settings.resolution_watcher_interval_seconds = 1  # Fast polling for test
        settings.mock_integrations = True
        mock_settings.return_value = settings

        with patch('src.agents.resolution_watcher.NotifyAgent'):
            watcher = ResolutionWatcher()
            watcher._stop_event = asyncio.Event()

            poll_count = 0

            async def mock_poll_once():
                nonlocal poll_count
                poll_count += 1

            with patch.object(watcher, "_poll_once", side_effect=mock_poll_once):
                # Start polling in background
                polling_task = asyncio.create_task(watcher._polling_loop())

                # Let it poll once
                await asyncio.sleep(0.2)

                # Stop it
                watcher._stop_event.set()
                await polling_task

                # Should have polled at least once
                assert poll_count >= 1


@pytest.mark.asyncio
async def test_polling_loop_handles_exceptions():
    """Test polling loop continues after exceptions."""
    with patch('src.agents.resolution_watcher.get_settings') as mock_settings:
        settings = MagicMock()
        settings.trello_api_key = "test-key"
        settings.trello_api_token = "test-token"
        settings.trello_done_list_id = "DONE"
        settings.resolution_watcher_interval_seconds = 0.1  # Very fast for test
        settings.mock_integrations = True
        mock_settings.return_value = settings

        with patch('src.agents.resolution_watcher.NotifyAgent'):
            watcher = ResolutionWatcher()
            watcher._stop_event = asyncio.Event()

            call_count = 0

            async def mock_poll_once():
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise Exception("Test error")
                # Don't raise on second call

            with patch.object(watcher, "_poll_once", side_effect=mock_poll_once):
                polling_task = asyncio.create_task(watcher._polling_loop())

                # Let it run for a bit
                await asyncio.sleep(0.3)

                watcher._stop_event.set()
                await polling_task

                # Should have been called multiple times despite error
                assert call_count >= 2


@pytest.mark.asyncio
async def test_iteration_counter_increments():
    """Test that polling iteration counter increments."""
    with patch('src.agents.resolution_watcher.get_settings') as mock_settings:
        settings = MagicMock()
        settings.trello_api_key = "test-key"
        settings.trello_api_token = "test-token"
        settings.trello_done_list_id = "DONE"
        settings.resolution_watcher_interval_seconds = 60
        settings.mock_integrations = True
        mock_settings.return_value = settings

        with patch('src.agents.resolution_watcher.NotifyAgent'):
            watcher = ResolutionWatcher()
            assert watcher._iteration_count == 0

            with patch.object(
                watcher, "_get_unresolved_tickets", return_value=[]
            ):
                await watcher._poll_once()
                assert watcher._iteration_count == 1

                await watcher._poll_once()
                assert watcher._iteration_count == 2
