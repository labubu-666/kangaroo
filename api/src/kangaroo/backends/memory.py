from typing import Any, ClassVar
from uuid import UUID, uuid7

from pydantic import BaseModel

from kangaroo.backends.base import (
    BaseBackend,
    BoardSpec,
    FunctionSpec,
    ProjectSpec,
    StatusSpec,
    StatusTransitionSpec,
    WorkItemSpec,
    WorkItemTypeSpec,
    matches_search,
    new_work_item_fields,
    utc_now,
)
from kangaroo.errors import NotFoundError
from kangaroo.schemas import (
    Board,
    BoardCreate,
    BoardReplace,
    BoardUpdate,
    Function,
    FunctionCreate,
    FunctionReplace,
    FunctionUpdate,
    Project,
    ProjectCreate,
    ProjectReplace,
    ProjectStatus,
    ProjectUpdate,
    StatusCreate,
    StatusReplace,
    StatusTransition,
    StatusTransitionCreate,
    StatusTransitionReplace,
    StatusTransitionUpdate,
    StatusUpdate,
    WorkItem,
    WorkItemCreate,
    WorkItemReplace,
    WorkItemType,
    WorkItemTypeCreate,
    WorkItemTypeReplace,
    WorkItemTypeUpdate,
    WorkItemUpdate,
)


class InMemoryBackend[M: BaseModel, C: BaseModel, U: BaseModel, R: BaseModel](
    BaseBackend[M, C, U, R]
):
    """Generic in-memory storage backed by a dict keyed by ID."""

    model_type: ClassVar[type[BaseModel]]

    def __init__(self) -> None:
        self._items: dict[UUID, M] = {}

    def _build(self, item: C) -> M:
        """Build a new stored model from a create request."""
        now = utc_now()
        return self.model_type(  # type: ignore[return-value]
            id=uuid7(), created_at=now, modified_at=now, **item.model_dump()
        )

    def create(self, item: C) -> M:
        """Create a new entity in memory."""
        built = self._build(item)
        self._items[built.id] = built  # type: ignore[attr-defined]
        return built

    def get_by_id(self, item_id: UUID) -> M:
        """Get an entity by ID."""
        if item_id not in self._items:
            raise NotFoundError(f"{self.entity} {item_id} not found")
        return self._items[item_id]

    def update(self, item_id: UUID, update: U) -> M:
        """Update an entity (partial update)."""
        existing = self.get_by_id(item_id)
        updated = existing.model_copy(
            update={
                **update.model_dump(exclude_unset=True),
                "modified_at": utc_now(),
            }
        )
        self._items[item_id] = updated  # type: ignore[assignment]
        return updated  # type: ignore[return-value]

    def replace(self, item_id: UUID, replace: R) -> M:
        """Replace an entity (full update), keeping its ID and created_at."""
        existing = self.get_by_id(item_id)
        replaced = existing.model_copy(
            update={**replace.model_dump(), "modified_at": utc_now()}
        )
        self._items[item_id] = replaced  # type: ignore[assignment]
        return replaced  # type: ignore[return-value]

    def delete(self, item_id: UUID) -> None:
        """Delete an entity."""
        self.get_by_id(item_id)
        del self._items[item_id]

    def _matches(self, item: M, filters: dict[str, Any], search: str | None) -> bool:
        if not all(
            getattr(item, name, None) == value for name, value in filters.items()
        ):
            return False
        return search is None or matches_search(item, search, self.search_fields)

    def _select(
        self,
        filters: dict[str, Any],
        search: str | None,
        limit: int | None,
        offset: int,
    ) -> list[M]:
        matching = [
            item
            for item in self._items.values()
            if self._matches(item, filters, search)
        ]
        end = None if limit is None else offset + limit
        return matching[offset:end]

    def _count(self, filters: dict[str, Any], search: str | None) -> int:
        return len(self._select(filters, search, None, 0))


class InMemoryProjectBackend(
    ProjectSpec,
    InMemoryBackend[Project, ProjectCreate, ProjectUpdate, ProjectReplace],
):
    """In-memory project storage."""

    model_type = Project


class InMemoryBoardBackend(
    BoardSpec,
    InMemoryBackend[Board, BoardCreate, BoardUpdate, BoardReplace],
):
    """In-memory board storage."""

    model_type = Board


class InMemoryStatusBackend(
    StatusSpec,
    InMemoryBackend[ProjectStatus, StatusCreate, StatusUpdate, StatusReplace],
):
    """In-memory status storage."""

    model_type = ProjectStatus


class InMemoryWorkItemTypeBackend(
    WorkItemTypeSpec,
    InMemoryBackend[
        WorkItemType, WorkItemTypeCreate, WorkItemTypeUpdate, WorkItemTypeReplace
    ],
):
    """In-memory work item type storage."""

    model_type = WorkItemType


class InMemoryStatusTransitionBackend(
    StatusTransitionSpec,
    InMemoryBackend[
        StatusTransition,
        StatusTransitionCreate,
        StatusTransitionUpdate,
        StatusTransitionReplace,
    ],
):
    """In-memory status transition storage."""

    model_type = StatusTransition


class InMemoryWorkItemBackend(
    WorkItemSpec,
    InMemoryBackend[WorkItem, WorkItemCreate, WorkItemUpdate, WorkItemReplace],
):
    """In-memory work item storage."""

    model_type = WorkItem

    def _build(self, item: WorkItemCreate) -> WorkItem:
        return WorkItem(**new_work_item_fields(item))


class InMemoryFunctionBackend(
    FunctionSpec,
    InMemoryBackend[Function, FunctionCreate, FunctionUpdate, FunctionReplace],
):
    """In-memory function storage."""

    model_type = Function
