from typing import Any

from kangaroo.repositories import RecentHistoryRepository
from kangaroo.schemas import RecentEntry, RecentEntryCreate
from kangaroo.services.api_keys import owner_id

SHOWN = 10
SAVED = 100


class RecentHistoryService:
    """Each user's recent items. Up to SAVED are kept, and SHOWN are returned."""

    def __init__(self, history: RecentHistoryRepository) -> None:
        self._history = history

    def record(self, user: dict[str, Any], entry: RecentEntryCreate) -> None:
        self._history.upsert(owner_id(user), entry)

    def list_for(self, user: dict[str, Any], search: str | None) -> list[RecentEntry]:
        """Return the newest matches up to SHOWN."""
        rows = self._history.list_for(owner_id(user), search, limit=SHOWN)
        return [RecentEntry.model_validate(row, from_attributes=True) for row in rows]

    def prune(self) -> None:
        """Keep only the newest SAVED entries of every user."""
        self._history.prune(keep=SAVED)

    def remove(self, user: dict[str, Any], type: str, item_id: str) -> None:
        self._history.delete(owner_id(user), type, item_id)

    def clear(self, user: dict[str, Any]) -> None:
        self._history.clear(owner_id(user))
