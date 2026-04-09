"""Application configuration — loaded from environment variables via python-dotenv."""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # App
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info").upper()

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/incidents.db")

    # Anthropic
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

    # Trello
    TRELLO_API_KEY: str = os.getenv("TRELLO_API_KEY", "")
    TRELLO_API_TOKEN: str = os.getenv("TRELLO_API_TOKEN", "")
    TRELLO_BOARD_ID: str = os.getenv("TRELLO_BOARD_ID", "")
    TRELLO_LIST_ID: str = os.getenv("TRELLO_LIST_ID", "")
    TRELLO_DONE_LIST_ID: str = os.getenv("TRELLO_DONE_LIST_ID", "")

    # Slack
    SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")
    SLACK_CHANNEL: str = os.getenv("SLACK_CHANNEL", "#incidents")

    # SendGrid
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    SENDGRID_FROM_EMAIL: str = os.getenv("SENDGRID_FROM_EMAIL", "sre-agent@example.com")
    SENDGRID_FROM_NAME: str = os.getenv("SENDGRID_FROM_NAME", "SRE Agent")

    # Mock mode — set MOCK_INTEGRATIONS=true to skip real API calls
    MOCK_INTEGRATIONS: bool = os.getenv("MOCK_INTEGRATIONS", "false").lower() == "true"

    # File storage
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))

    # Medusa.js repo path (mounted as Docker volume)
    MEDUSA_REPO_PATH: str = os.getenv("MEDUSA_REPO_PATH", "./medusa-repo")

    # ResolutionWatcher
    RESOLUTION_WATCHER_INTERVAL_SECONDS: int = int(
        os.getenv("RESOLUTION_WATCHER_INTERVAL_SECONDS", "60")
    )

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


settings = Settings()
