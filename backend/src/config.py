"""
Configuration management for the application.

Handles environment variables, database settings, and API credentials.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Anthropic
    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-4-6"

    # Trello
    trello_api_key: str = ""
    trello_api_token: str = ""
    trello_board_id: str = ""
    trello_list_id: str = ""
    trello_done_list_id: str = ""

    # Slack
    slack_webhook_url: str = ""

    # SendGrid
    sendgrid_api_key: str = ""
    reporter_email_from: str = "sre-agent@company.com"
    mock_email: bool = False

    # Database
    database_url: str = "sqlite:///./data/incidents.db"

    # App
    app_port: int = 8000
    log_level: str = "INFO"
    log_file: str = "/app/logs/agent.log"

    # E-commerce
    ecommerce_repo_path: str = "/app/medusa-repo"

    # Demo / mock mode
    mock_integrations: bool = False

    # Resolution watcher
    resolution_watcher_interval_seconds: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
