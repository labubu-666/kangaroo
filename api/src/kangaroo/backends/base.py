from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any, ClassVar
from uuid import UUID, uuid7

from pydantic import BaseModel

from kangaroo.schemas import (
    Board,
    BoardCreate,
    BoardReplace,
    BoardUpdate,
    Function,
    FunctionCreate,
    FunctionReplace,
    FunctionUpdate,
    PaginatedResponse,
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


class BaseBackend[M: BaseModel, C: BaseModel, U: BaseModel, R: BaseModel](ABC):
    """Storage for one kind of entity.

    M is the stored model, C the create request, U the partial update and R the
    full replacement. Subclasses set ``entity`` (used in error messages) and
    ``filter_fields`` (the only names that list and count filters may use) and
    ``search_fields`` (the text fields a free-text search matches against).
    """

    entity: ClassVar[str]
    filter_fields: ClassVar[frozenset[str]]
    search_fields: ClassVar[tuple[str, ...]]

    @abstractmethod
    def create(self, item: C) -> M:
        """Create a new entity with an assigned ID and metadata."""

    @abstractmethod
    def bind(self, session: Any) -> BaseBackend[M, C, U, R]:
        """Return a copy of this backend whose calls all run inside ``session``."""

    @abstractmethod
    def get_by_id(self, item_id: UUID) -> M:
        """Return the entity with the given ID.

        Raises:
            NotFoundError: If the entity does not exist.
        """

    @abstractmethod
    def update(self, item_id: UUID, update: U) -> M:
        """Partially update an entity.

        Raises:
            NotFoundError: If the entity does not exist.
        """

    @abstractmethod
    def replace(self, item_id: UUID, replace: R) -> M:
        """Fully replace an entity.

        Raises:
            NotFoundError: If the entity does not exist.
        """

    @abstractmethod
    def delete(self, item_id: UUID) -> None:
        """Delete an entity.

        Raises:
            NotFoundError: If the entity does not exist.
        """

    @abstractmethod
    def _select(
        self,
        filters: dict[str, Any],
        search: str | None,
        limit: int | None,
        offset: int,
    ) -> list[M]:
        """Return the entities matching the filters and search text, in order."""

    @abstractmethod
    def _count(self, filters: dict[str, Any], search: str | None) -> int:
        """Count the entities matching the filters and search text."""

    def list_all(self, **filters: Any) -> list[M]:
        """Return all entities matching the filters.

        Filters are exact matches on ``filter_fields``. A filter set to None is
        ignored.

        Raises:
            ValueError: If a filter name is not one of ``filter_fields``.
        """
        return self._select(self._checked(filters), None, None, 0)

    def list_paginated(
        self, limit: int, offset: int, search: str | None = None, **filters: Any
    ) -> PaginatedResponse[M]:
        """Return a page of entities matching the filters and search, plus the total.

        ``search`` is a case-insensitive substring match on any of ``search_fields``.
        A blank search is ignored.

        Raises:
            ValueError: If a filter name is not one of ``filter_fields``.
        """
        checked = self._checked(filters)
        text = clean_search(search)
        return PaginatedResponse[M](
            results=self._select(checked, text, limit, offset),
            limit=limit,
            offset=offset,
            total=self._count(checked, text),
        )

    def count(self, **filters: Any) -> int:
        """Count entities matching the filters.

        Raises:
            ValueError: If a filter name is not one of ``filter_fields``.
        """
        return self._count(self._checked(filters), None)

    def _checked(self, filters: dict[str, Any]) -> dict[str, Any]:
        """Reject unknown filter names, then drop filters that are None."""
        for name in filters:
            if name not in self.filter_fields:
                raise ValueError(f"Unknown filter field {name!r} for {self.entity}")
        return {name: value for name, value in filters.items() if value is not None}


def clean_search(search: str | None) -> str | None:
    """Strip the search text, treating blank text as no search."""
    if search is None or not search.strip():
        return None
    return search.strip()


def matches_search(item: BaseModel, text: str, fields: tuple[str, ...]) -> bool:
    """Case-insensitive substring match of ``text`` on any of ``fields``."""
    needle = text.lower()
    return any(needle in (getattr(item, name, None) or "").lower() for name in fields)


def utc_now() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""
    return datetime.now(UTC)


def new_work_item_fields(item: WorkItemCreate) -> dict[str, Any]:
    """Return the stored fields for a new work item, shared by all backends.

    The service fills in ``status_id`` before it reaches the backend.
    """
    if item.status_id is None:
        raise ValueError("status_id must be set before a work item is stored")
    now = utc_now()
    return {
        "id": uuid7(),
        "title": item.title,
        "description": item.description,
        "project_id": item.project_id,
        "type_id": item.type_id,
        "status_id": item.status_id,
        "parent_id": item.parent_id,
        "labels": item.labels,
        "trashed": False,
        "created_at": now,
        "modified_at": now,
    }


WorkItemBackend = BaseBackend[WorkItem, WorkItemCreate, WorkItemUpdate, WorkItemReplace]
ProjectBackend = BaseBackend[Project, ProjectCreate, ProjectUpdate, ProjectReplace]
BoardBackend = BaseBackend[Board, BoardCreate, BoardUpdate, BoardReplace]
FunctionBackend = BaseBackend[Function, FunctionCreate, FunctionUpdate, FunctionReplace]
StatusBackend = BaseBackend[ProjectStatus, StatusCreate, StatusUpdate, StatusReplace]
WorkItemTypeBackend = BaseBackend[
    WorkItemType, WorkItemTypeCreate, WorkItemTypeUpdate, WorkItemTypeReplace
]
StatusTransitionBackend = BaseBackend[
    StatusTransition,
    StatusTransitionCreate,
    StatusTransitionUpdate,
    StatusTransitionReplace,
]
