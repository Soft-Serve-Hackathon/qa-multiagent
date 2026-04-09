"""Application configuration — loaded from environment variables via python-dotenv."""
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def _resolve_medusa_repo_path() -> str:
    """Resolve Medusa repo path from env, relative to project root when needed."""
    raw = os.getenv("MEDUSA_REPO_PATH", os.getenv("ECOMMERCE_REPO_PATH", "./medusa-repo"))
    candidate = Path(raw)
    if candidate.is_absolute():
        return str(candidate)

    # config.py is in backend/src, so project root is two levels up from backend/
    project_root = Path(__file__).resolve().parents[2]
    return str((project_root / candidate).resolve())


def _parse_owner_routing() -> dict:
    """Parse owner routing JSON from env. Returns empty mapping on invalid JSON."""
    raw = os.getenv("OWNER_ROUTING_JSON", "{}").strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


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
    # Backward compatible with legacy ECOMMERCE_REPO_PATH name.
    MEDUSA_REPO_PATH: str = _resolve_medusa_repo_path()

    # ResolutionWatcher
    RESOLUTION_WATCHER_INTERVAL_SECONDS: int = int(
        os.getenv("RESOLUTION_WATCHER_INTERVAL_SECONDS", "60")
    )

    # Owner routing by module for Trello + Slack assignment.
    # Example:
    # {
    #   "cart": {"trello_member_id": "abc123", "slack_user_id": "U012345"},
    #   "default": {"trello_member_id": "xyz789", "slack_user_id": "U098765"}
    # }
    OWNER_ROUTING: dict = _parse_owner_routing()

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


settings = Settings()
