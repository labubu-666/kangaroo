from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, ClassVar
from uuid import UUID, uuid7

from pydantic import BaseModel
from sqlalchemy import (
    Engine,
    Select,
    func,
    or_,
    select,
)
from sqlalchemy.orm import Session

from kangaroo.backends.base import (
    BaseBackend,
    new_work_item_fields,
    utc_now,
)
from kangaroo.backends.sqlite.tables import (
    Base,
    BoardRow,
    FunctionRow,
    ProjectRow,
    StatusRow,
    StatusTransitionRow,
    WorkItemRow,
    WorkItemTypeRow,
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


def _escape_like(text: str) -> str:
    """Escape LIKE wildcards so the search text is matched literally."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _model_from_row[M: BaseModel](model: type[M], row: Base) -> M:
    return model.model_validate(row, from_attributes=True)


class SQLiteBackend[M: BaseModel, C: BaseModel, U: BaseModel, R: BaseModel](
    BaseBackend[M, C, U, R]
):
    """Generic SQLite storage using one table per entity type."""

    model_type: ClassVar[type[BaseModel]]
    row_type: ClassVar[type[Base]]

    def __init__(self, engine: Engine, session: Session | None = None) -> None:
        """Use ``session`` for every call if given; otherwise open one per call."""
        self._engine = engine
        self._session = session

    def bind(self, session: Session) -> SQLiteBackend[M, C, U, R]:
        """A copy of this backend that runs every call inside ``session``."""
        return type(self)(self._engine, session)

    @contextmanager
    def _scope(self, write: bool = False) -> Generator[Session]:
        """The bound session, or a new one that commits when ``write`` is set.

        A bound session is left alone: the request that owns it decides when to
        commit or roll back.
        """
        if self._session is not None:
            yield self._session
            return
        with Session(self._engine, expire_on_commit=False) as own:
            yield own
            if write:
                own.commit()

    def _new_row(self, item: C) -> Base:
        """Build a new row from a create request."""
        now = utc_now()
        return self.row_type(
            id=uuid7(), created_at=now, modified_at=now, **item.model_dump()
        )

    def _to_model(self, row: Base) -> M:
        return _model_from_row(self.model_type, row)  # type: ignore[return-value]

    def _get_row(self, session: Session, item_id: UUID) -> Base:
        row = session.get(self.row_type, item_id)
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
        with self._scope(write=True) as session:
            row = self._new_row(item)
            session.add(row)
            session.flush()
            return self._to_model(row)

    def get_by_id(self, item_id: UUID) -> M:
        """Get an entity by ID."""
        with self._scope() as session:
            return self._to_model(self._get_row(session, item_id))

    def update(self, item_id: UUID, update: U) -> M:
        """Update an entity (partial update)."""
        with self._scope(write=True) as session:
            row = self._get_row(session, item_id)
            for field, value in update.model_dump(exclude_unset=True).items():
                setattr(row, field, value)
            row.modified_at = utc_now()
            session.flush()
            return self._to_model(row)

    def replace(self, item_id: UUID, replace: R) -> M:
        """Replace an entity (full update), keeping its ID and created_at."""
        with self._scope(write=True) as session:
            row = self._get_row(session, item_id)
            for field, value in replace.model_dump().items():
                setattr(row, field, value)
            row.modified_at = utc_now()
            session.flush()
            return self._to_model(row)

    def delete(self, item_id: UUID) -> None:
        """Delete an entity.

        Foreign keys (ON DELETE RESTRICT) block deleting rows that still have
        dependants; the service layer checks this first.
        """
        with self._scope(write=True) as session:
            session.delete(self._get_row(session, item_id))
            session.flush()

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
        with self._scope() as session:
            rows = session.scalars(stmt.offset(offset)).all()
            return [self._to_model(row) for row in rows]

    def _count(self, filters: dict[str, Any], search: str | None) -> int:
        stmt = select(func.count()).select_from(self._query(filters, search).subquery())
        with self._scope() as session:
            return session.scalar(stmt) or 0


class SQLiteProjectBackend(
    SQLiteBackend[Project, ProjectCreate, ProjectUpdate, ProjectReplace]
):
    """SQLite project storage."""

    entity = "Project"
    filter_fields = frozenset(Project.model_fields)
    search_fields = ("name", "description")
    model_type = Project
    row_type = ProjectRow


class SQLiteBoardBackend(SQLiteBackend[Board, BoardCreate, BoardUpdate, BoardReplace]):
    """SQLite board storage."""

    entity = "Board"
    filter_fields = frozenset(Board.model_fields)
    search_fields = ("name", "description")
    model_type = Board
    row_type = BoardRow


class SQLiteStatusBackend(
    SQLiteBackend[ProjectStatus, StatusCreate, StatusUpdate, StatusReplace]
):
    """SQLite status storage."""

    entity = "Status"
    filter_fields = frozenset(ProjectStatus.model_fields)
    search_fields = ("name",)
    model_type = ProjectStatus
    row_type = StatusRow


class SQLiteWorkItemTypeBackend(
    SQLiteBackend[
        WorkItemType, WorkItemTypeCreate, WorkItemTypeUpdate, WorkItemTypeReplace
    ]
):
    """SQLite work item type storage."""

    entity = "Work item type"
    filter_fields = frozenset(WorkItemType.model_fields)
    search_fields = ("name",)
    model_type = WorkItemType
    row_type = WorkItemTypeRow


class SQLiteStatusTransitionBackend(
    SQLiteBackend[
        StatusTransition,
        StatusTransitionCreate,
        StatusTransitionUpdate,
        StatusTransitionReplace,
    ]
):
    """SQLite status transition storage."""

    entity = "Status transition"
    filter_fields = frozenset(StatusTransition.model_fields)
    search_fields = ()
    model_type = StatusTransition
    row_type = StatusTransitionRow


class SQLiteWorkItemBackend(
    SQLiteBackend[WorkItem, WorkItemCreate, WorkItemUpdate, WorkItemReplace]
):
    """SQLite work item storage."""

    entity = "Work item"
    filter_fields = frozenset(WorkItem.model_fields)
    search_fields = ("title", "description")
    model_type = WorkItem
    row_type = WorkItemRow

    def _new_row(self, item: WorkItemCreate) -> WorkItemRow:
        return WorkItemRow(**new_work_item_fields(item))


class SQLiteFunctionBackend(
    SQLiteBackend[Function, FunctionCreate, FunctionUpdate, FunctionReplace]
):
    """SQLite function storage."""

    entity = "Function"
    filter_fields = frozenset(Function.model_fields)
    search_fields = ("name", "description")
    model_type = Function
    row_type = FunctionRow
