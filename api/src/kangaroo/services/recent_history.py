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
        """Trim the stored history to SAVED, then return the newest matches up to SHOWN.

        Trimming happens on every read so storage never grows past SAVED per user.
        """
        owner = owner_id(user)
        self._history.truncate(owner, keep=SAVED)
        rows = self._history.list_for(owner, search, limit=SHOWN)
        return [RecentEntry.model_validate(row, from_attributes=True) for row in rows]

    def remove(self, user: dict[str, Any], type: str, item_id: str) -> None:
        self._history.delete(owner_id(user), type, item_id)

    def clear(self, user: dict[str, Any]) -> None:
        self._history.clear(owner_id(user))
