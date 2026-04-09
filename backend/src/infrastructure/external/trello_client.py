"""Trello REST API client — creates and monitors incident cards."""
import requests
from src.config import settings

TRELLO_BASE = "https://api.trello.com/1"


class TrelloClient:
    def __init__(self):
        self._key = settings.TRELLO_API_KEY
        self._token = settings.TRELLO_API_TOKEN
        self._mock = settings.MOCK_INTEGRATIONS

    def _auth_params(self) -> dict:
        return {"key": self._key, "token": self._token}

    def create_card(
        self,
        title: str,
        description: str,
        list_id: str,
        label_color: str = "orange",
    ) -> dict:
        """Create a Trello card. Returns {card_id, card_url}."""
        if self._mock:
            import uuid
            card_id = f"mock-trello-{uuid.uuid4().hex[:8]}"
            return {
                "card_id": card_id,
                "card_url": f"https://trello.com/c/{card_id}",
                "is_mock": True,
                "mock_board": "🎭 MOCK Incident Board",
                "mock_title": title,
            }

        params = {**self._auth_params(), "idList": list_id, "name": title, "desc": description}
        resp = requests.post(f"{TRELLO_BASE}/cards", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return {"card_id": data["id"], "card_url": data["shortUrl"], "is_mock": False}

    def add_checklist(self, card_id: str, name: str, items: list[str]) -> None:
        """Add a checklist to an existing card."""
        if self._mock:
            return

        params = {**self._auth_params(), "idCard": card_id, "name": name}
        resp = requests.post(f"{TRELLO_BASE}/checklists", params=params, timeout=10)
        resp.raise_for_status()
        checklist_id = resp.json()["id"]

        for item in items:
            requests.post(
                f"{TRELLO_BASE}/checklists/{checklist_id}/checkItems",
                params={**self._auth_params(), "name": item},
                timeout=10,
            )

    def get_cards_in_list(self, list_id: str) -> list[dict]:
        """Fetch all cards in a Trello list (used by ResolutionWatcher)."""
        if self._mock:
            return []

        params = {**self._auth_params(), "fields": "id,name,idList"}
        resp = requests.get(f"{TRELLO_BASE}/lists/{list_id}/cards", params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
