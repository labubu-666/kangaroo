from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, status

from kangaroo.routes.auth import require_user
from kangaroo.routes.dependencies import RecentHistoryServiceDep
from kangaroo.schemas import RecentEntry, RecentEntryCreate, RecentType

router = APIRouter(prefix="/recent-history", tags=["recent-history"])

UserDep = Annotated[dict[str, Any], Depends(require_user)]


@router.get("/", response_model=list[RecentEntry])
def list_recent_history(
    service: RecentHistoryServiceDep,
    user: UserDep,
    search: str | None = Query(default=None, max_length=200),
) -> list[RecentEntry]:
    """Return your 10 most recent items, newest first. Older items beyond 100 are dropped.

    With ``search``, match titles and parents across everything saved.
    """
    return service.list_for(user, search)


@router.post("/", status_code=status.HTTP_204_NO_CONTENT)
def record_recent_visit(
    entry: RecentEntryCreate,
    service: RecentHistoryServiceDep,
    user: UserDep,
) -> None:
    """Record that you opened an item. A repeat visit moves it to the top."""
    service.record(user, entry)


@router.delete("/{type}/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_recent_entry(
    type: RecentType,
    item_id: str,
    service: RecentHistoryServiceDep,
    user: UserDep,
) -> None:
    """Remove one item from your recent history."""
    service.remove(user, type, item_id)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def clear_recent_history(service: RecentHistoryServiceDep, user: UserDep) -> None:
    """Clear your recent history."""
    service.clear(user)
