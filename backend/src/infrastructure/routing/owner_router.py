"""Owner routing helper — maps affected modules to Trello/Slack owners."""
from src.config import settings


def resolve_owner(affected_module: str) -> dict:
    """Return owner mapping for module with fallback to default entry."""
    routing = settings.OWNER_ROUTING or {}
    module_key = (affected_module or "").lower().strip()

    owner = routing.get(module_key) or routing.get("default") or {}
    return {
        "trello_member_id": owner.get("trello_member_id"),
        "slack_user_id": owner.get("slack_user_id"),
    }
