from datetime import UTC, datetime
from typing import Any, ClassVar
from uuid import UUID, uuid7

from pydantic import BaseModel
from sqlalchemy import (
    Select,
    func,
    or_,
    select,
)
from sqlalchemy.orm import Session

from kangaroo.errors import NotFoundError
from kangaroo.repositories.tables import (
    Base,
    BoardRow,
    FunctionRow,
    InvocationRow,
    ProjectRow,
    StatusRow,
    StatusTransitionRow,
    WorkItemRow,
    WorkItemTypeRow,
)
from kangaroo.schemas import (
    Board,
    BoardCreate,
    BoardReplace,
    BoardUpdate,
    Function,
    FunctionCreate,
    FunctionReplace,
    FunctionUpdate,
    Invocation,
    InvocationCreate,
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
    """Return the stored fields for a new work item.

    The service fills in ``status_id`` before it reaches the repository.
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


def _escape_like(text: str) -> str:
    """Escape LIKE wildcards so the search text is matched literally."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _model_from_row[M: BaseModel](model: type[M], row: Base) -> M:
    return model.model_validate(row, from_attributes=True)


class Repository[M: BaseModel, C: BaseModel, U: BaseModel, R: BaseModel]:
    """Storage for one kind of entity, using one table per entity type.

    M is the stored model, C the create request, U the partial update and R the
    full replacement. Subclasses set ``entity`` (used in error messages),
    ``filter_fields`` (the only names that list and count filters may use),
    ``search_fields`` (the text fields a free-text search matches against),
    ``model_type`` and ``row_type``.

    Every call runs inside the session the repository was given. The caller
    decides when to commit or roll back.
    """

    entity: ClassVar[str]
    filter_fields: ClassVar[frozenset[str]]
    search_fields: ClassVar[tuple[str, ...]]
    model_type: ClassVar[type[BaseModel]]
    row_type: ClassVar[type[Base]]

    def __init__(self, session: Session) -> None:
        self._session = session

    def _new_row(self, item: C) -> Base:
        """Build a new row from a create request."""
        now = utc_now()
        return self.row_type(
            id=uuid7(), created_at=now, modified_at=now, **item.model_dump()
        )

    def _to_model(self, row: Base) -> M:
        return _model_from_row(self.model_type, row)  # type: ignore[return-value]

    def _get_row(self, item_id: UUID) -> Base:
        row = self._session.get(self.row_type, item_id)
        if row is None:
            raise NotFoundError(f"{self.entity} {item_id} not found")
        return row

    def _query(self, filters: dict[str, Any], search: str | None) -> Select:
        stmt = select(self.row_type).order_by(
            self.row_type.created_at, self.row_type.id
        )
        for name, value in filters.items():
            stmt = stmt.where(getattr(self.row_type, name) == value)
        if search is not None:
            pattern = f"%{_escape_like(search)}%"
            stmt = stmt.where(
                or_(
                    *(
                        getattr(self.row_type, name).ilike(pattern, escape="\\")
                        for name in self.search_fields
                    )
                )
            )
        return stmt

    def create(self, item: C) -> M:
        """Create a new entity."""
        row = self._new_row(item)
        self._session.add(row)
        self._session.flush()
        return self._to_model(row)

    def get_by_id(self, item_id: UUID) -> M:
        """Return the entity with the given ID.

        Raises:
            NotFoundError: If the entity does not exist.
        """
        return self._to_model(self._get_row(item_id))

    def update(self, item_id: UUID, update: U) -> M:
        """Partially update an entity.

        Raises:
            NotFoundError: If the entity does not exist.
        """
        row = self._get_row(item_id)
        for field, value in update.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        row.modified_at = utc_now()
        self._session.flush()
        return self._to_model(row)

    def replace(self, item_id: UUID, replace: R) -> M:
        """Fully replace an entity, keeping its ID and created_at.

        Raises:
            NotFoundError: If the entity does not exist.
        """
        row = self._get_row(item_id)
        for field, value in replace.model_dump().items():
            setattr(row, field, value)
        row.modified_at = utc_now()
        self._session.flush()
        return self._to_model(row)

    def delete(self, item_id: UUID) -> None:
        """Delete an entity.

        Foreign keys (ON DELETE RESTRICT) block deleting rows that still have
        dependants; the service layer checks this first.

        Raises:
            NotFoundError: If the entity does not exist.
        """
        self._session.delete(self._get_row(item_id))
        self._session.flush()

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

    def _select(
        self,
        filters: dict[str, Any],
        search: str | None,
        limit: int | None,
        offset: int,
    ) -> list[M]:
        stmt = self._query(filters, search)
        if limit is not None:
            stmt = stmt.limit(limit)
        rows = self._session.scalars(stmt.offset(offset)).all()
        return [self._to_model(row) for row in rows]

    def _count(self, filters: dict[str, Any], search: str | None) -> int:
        stmt = select(func.count()).select_from(self._query(filters, search).subquery())
        return self._session.scalar(stmt) or 0


class ProjectRepository(
    Repository[Project, ProjectCreate, ProjectUpdate, ProjectReplace]
):
    """Project storage."""

    entity = "Project"
    filter_fields = frozenset(Project.model_fields)
    search_fields = ("name", "description")
    model_type = Project
    row_type = ProjectRow


class BoardRepository(Repository[Board, BoardCreate, BoardUpdate, BoardReplace]):
    """Board storage."""

    entity = "Board"
    filter_fields = frozenset(Board.model_fields)
    search_fields = ("name", "description")
    model_type = Board
    row_type = BoardRow


class StatusRepository(
    Repository[ProjectStatus, StatusCreate, StatusUpdate, StatusReplace]
):
    """Status storage."""

    entity = "Status"
    filter_fields = frozenset(ProjectStatus.model_fields)
    search_fields = ("name",)
    model_type = ProjectStatus
    row_type = StatusRow


class WorkItemTypeRepository(
    Repository[
        WorkItemType, WorkItemTypeCreate, WorkItemTypeUpdate, WorkItemTypeReplace
    ]
):
    """Work item type storage."""

    entity = "Work item type"
    filter_fields = frozenset(WorkItemType.model_fields)
    search_fields = ("name",)
    model_type = WorkItemType
    row_type = WorkItemTypeRow


class StatusTransitionRepository(
    Repository[
        StatusTransition,
        StatusTransitionCreate,
        StatusTransitionUpdate,
        StatusTransitionReplace,
    ]
):
    """Status transition storage."""

    entity = "Status transition"
    filter_fields = frozenset(StatusTransition.model_fields)
    search_fields = ()
    model_type = StatusTransition
    row_type = StatusTransitionRow


class WorkItemRepository(
    Repository[WorkItem, WorkItemCreate, WorkItemUpdate, WorkItemReplace]
):
    """Work item storage."""

    entity = "Work item"
    filter_fields = frozenset(WorkItem.model_fields)
    search_fields = ("title", "description")
    model_type = WorkItem
    row_type = WorkItemRow

    def _new_row(self, item: WorkItemCreate) -> WorkItemRow:
        return WorkItemRow(**new_work_item_fields(item))


class FunctionRepository(
    Repository[Function, FunctionCreate, FunctionUpdate, FunctionReplace]
):
    """Function storage."""

    entity = "Function"
    filter_fields = frozenset(Function.model_fields)
    search_fields = ("name", "description")
    model_type = Function
    row_type = FunctionRow


class InvocationRepository(
    Repository[Invocation, InvocationCreate, InvocationCreate, InvocationCreate]
):
    """Invocation storage."""

    entity = "Invocation"
    filter_fields = frozenset({"function_id"})
    search_fields = ()
    model_type = Invocation
    row_type = InvocationRow
