import logging
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, ClassVar
from uuid import UUID, uuid7

from pydantic import BaseModel
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Engine,
    ForeignKey,
    Integer,
    Select,
    String,
    Uuid,
    create_engine,
    event,
    false,
    func,
    inspect,
    or_,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import TypeDecorator

from kangaroo.backends.base import (
    BaseBackend,
    BoardSpec,
    FunctionSpec,
    ProjectSpec,
    StatusSpec,
    StatusTransitionSpec,
    WorkItemSpec,
    WorkItemTypeSpec,
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
from kangaroo.templates import TO_DO_LIST


class UTCDateTime(TypeDecorator):
    """Store datetimes as naive UTC and read them back as aware UTC.

    SQLite has no timezone type, so the offset would otherwise be lost.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=UTC)


class Base(DeclarativeBase):
    """Declarative base for the SQLite tables."""

    trashed: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false()
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    modified_at: Mapped[datetime] = mapped_column(UTCDateTime)


class ProjectRow(Base):
    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    labels: Mapped[list[str]] = mapped_column(JSON, default=list, server_default="[]")


class WorkItemRow(Base):
    __tablename__ = "work_items"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    project_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    type_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("work_item_types.id", ondelete="RESTRICT"), nullable=False
    )
    status_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("statuses.id", ondelete="RESTRICT"), nullable=False
    )
    parent_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("work_items.id", ondelete="RESTRICT"), nullable=True
    )
    labels: Mapped[list[str]] = mapped_column(JSON, default=list, server_default="[]")


class BoardRow(Base):
    __tablename__ = "boards"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    filter: Mapped[str | None] = mapped_column(String, nullable=True)
    project_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    labels: Mapped[list[str]] = mapped_column(JSON, default=list, server_default="[]")


class WorkItemTypeRow(Base):
    __tablename__ = "work_item_types"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    project_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String)
    level: Mapped[str] = mapped_column(String)
    position: Mapped[int] = mapped_column(Integer)


class StatusRow(Base):
    __tablename__ = "statuses"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    project_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    position: Mapped[int] = mapped_column(Integer)


class StatusTransitionRow(Base):
    __tablename__ = "status_transitions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    project_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    from_status_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("statuses.id", ondelete="CASCADE"), nullable=False
    )
    to_status_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("statuses.id", ondelete="CASCADE"), nullable=False
    )


class FunctionRow(Base):
    __tablename__ = "functions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    code: Mapped[str] = mapped_column(String)
    labels: Mapped[list[str]] = mapped_column(JSON, default=list, server_default="[]")


def create_sqlite_engine(url: str) -> Engine:
    """Create a SQLAlchemy engine with foreign keys enabled and the schema ready.

    ``sqlite://memory`` maps to a shared in-memory database. Any other URL is
    passed to SQLAlchemy unchanged (e.g. ``sqlite:///kangaroo.db``).
    """
    if url == "sqlite://memory":
        engine = create_engine(
            "sqlite://",
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )
    else:
        engine = create_engine(url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    _add_missing_labels_column(engine)
    _migrate_to_project_templates(engine)
    return engine


def _add_missing_labels_column(engine: Engine) -> None:
    """Add the ``labels`` column to tables created before labels existed."""
    with engine.begin() as conn:
        for table in ("projects", "boards", "work_items"):
            columns = {column["name"] for column in inspect(conn).get_columns(table)}
            if "labels" not in columns:
                conn.exec_driver_sql(
                    f"ALTER TABLE {table} ADD COLUMN labels JSON NOT NULL DEFAULT '[]'"
                )


MIGRATION_LOG = logging.getLogger(__name__)

# Old string values in work_items, mapped to the names used by the To Do List template.
OLD_STATUS_NAMES = {"open": "Open", "in_progress": "In Progress", "done": "Done"}
OLD_TYPE_NAMES = {"task": "Task", "subtask": "Subtask"}


def _database_file(engine: Engine) -> Path | None:
    """The database file path, or None for an in-memory database."""
    database = engine.url.database
    if not database or database == ":memory:" or database.startswith("file::memory:"):
        return None
    return Path(database)


def _backup_database(engine: Engine, path: Path) -> Path:
    """Copy the database with SQLite's backup API, which includes WAL contents.

    Raises:
        sqlite3.Error: If the backup fails. The upgrade must then stop.
    """
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    target = path.with_name(f"{path.name}.pre-project-templates-{stamp}.bak")
    source = sqlite3.connect(path)
    try:
        destination = sqlite3.connect(target)
        try:
            source.backup(destination)
        finally:
            destination.close()
    finally:
        source.close()
    return target


def _needs_project_templates_upgrade(conn) -> bool:
    """True while work_items still has the old string ``status`` column."""
    columns = {column["name"] for column in inspect(conn).get_columns("work_items")}
    return "status" in columns


def _migrate_to_project_templates(engine: Engine) -> None:
    """One-off upgrade from fixed string statuses and types to project rows.

    Runs once, right after the schema is created. It backs up the database file,
    copies the To Do List statuses and types into every project that lacks them,
    and rebuilds ``work_items`` with ``status_id`` and ``type_id``. Any problem
    rolls the transaction back and leaves the data unchanged.
    """
    with engine.connect() as conn:
        if not _needs_project_templates_upgrade(conn):
            return
    path = _database_file(engine)
    if path is not None:
        backup = _backup_database(engine, path)
        MIGRATION_LOG.warning("Backed up database to %s", backup)

    raw = engine.raw_connection()
    try:
        cursor = raw.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.execute("BEGIN")
        try:
            _copy_template_rows(cursor)
            _rebuild_work_items(cursor)
            failures = cursor.execute("PRAGMA foreign_key_check").fetchall()
            if failures:
                raise RuntimeError(f"Foreign key check failed: {failures[:5]}")
            cursor.execute("COMMIT")
        except BaseException:
            cursor.execute("ROLLBACK")
            raise
        finally:
            cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        raw.close()


def _naive_utc(value: datetime) -> str:
    """Format a datetime the way UTCDateTime stores it: naive UTC text."""
    return value.astimezone(UTC).replace(tzinfo=None).isoformat(sep=" ")


def _copy_template_rows(cursor) -> None:
    """Give every project the To Do List types and statuses it does not have yet."""
    project_ids = [row[0] for row in cursor.execute("SELECT id FROM projects")]
    now = _naive_utc(utc_now())
    for project_id in project_ids:
        has_statuses = cursor.execute(
            "SELECT 1 FROM statuses WHERE project_id = ? LIMIT 1", (project_id,)
        ).fetchone()
        if has_statuses:
            continue
        for template_type in TO_DO_LIST.types:
            cursor.execute(
                "INSERT INTO work_item_types "
                "(id, project_id, name, level, position, created_at, modified_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    uuid7().hex,
                    project_id,
                    template_type.name,
                    template_type.level,
                    template_type.position,
                    now,
                    now,
                ),
            )
        for template_status in TO_DO_LIST.statuses:
            cursor.execute(
                "INSERT INTO statuses "
                "(id, project_id, name, category, position, created_at, modified_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    uuid7().hex,
                    project_id,
                    template_status.name,
                    template_status.category,
                    template_status.position,
                    now,
                    now,
                ),
            )


def _rebuild_work_items(cursor) -> None:
    """Replace work_items with the new layout, mapping each old value by name.

    Items whose status string is unknown go to their project's first To Do
    status, with a logged warning.
    """
    cursor.execute(
        "CREATE TABLE work_items_new ("
        "id CHAR(32) NOT NULL PRIMARY KEY, "
        "title VARCHAR NOT NULL, "
        "description VARCHAR, "
        "project_id CHAR(32) NOT NULL REFERENCES projects (id) ON DELETE RESTRICT, "
        "type_id CHAR(32) NOT NULL REFERENCES work_item_types (id) ON DELETE RESTRICT, "
        "status_id CHAR(32) NOT NULL REFERENCES statuses (id) ON DELETE RESTRICT, "
        "parent_id CHAR(32) REFERENCES work_items_new (id) ON DELETE RESTRICT, "
        "labels JSON NOT NULL DEFAULT '[]', "
        "trashed BOOLEAN NOT NULL DEFAULT 0, "
        "created_at DATETIME NOT NULL, "
        "modified_at DATETIME NOT NULL)"
    )
    rows = cursor.execute(
        "SELECT id, title, description, project_id, type, parent_id, status, "
        "labels, trashed, created_at, modified_at FROM work_items"
    ).fetchall()
    for row in rows:
        (
            item_id,
            title,
            description,
            project_id,
            old_type,
            parent_id,
            old_status,
            labels,
            trashed,
            created_at,
            modified_at,
        ) = row
        type_id = _template_row_id(
            cursor,
            "work_item_types",
            project_id,
            OLD_TYPE_NAMES[old_type] if old_type in OLD_TYPE_NAMES else None,
        )
        status_name = OLD_STATUS_NAMES.get(old_status)
        status_id = _template_row_id(cursor, "statuses", project_id, status_name)
        if status_id is None:
            MIGRATION_LOG.warning(
                "Work item %s has unknown status %r; moved to the first To Do status",
                item_id,
                old_status,
            )
            status_id = _first_todo_status(cursor, project_id)
        cursor.execute(
            "INSERT INTO work_items_new "
            "(id, title, description, project_id, type_id, status_id, parent_id, "
            "labels, trashed, created_at, modified_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                item_id,
                title,
                description,
                project_id,
                type_id,
                status_id,
                parent_id,
                labels,
                trashed,
                created_at,
                modified_at,
            ),
        )
    cursor.execute("DROP TABLE work_items")
    cursor.execute("ALTER TABLE work_items_new RENAME TO work_items")


def _template_row_id(cursor, table: str, project_id, name: str | None):
    """The ID of a project's status or type with this name, or None."""
    if name is None:
        return None
    row = cursor.execute(
        f"SELECT id FROM {table} WHERE project_id = ? AND name = ?",
        (project_id, name),
    ).fetchone()
    return row[0] if row else None


def _first_todo_status(cursor, project_id):
    row = cursor.execute(
        "SELECT id FROM statuses WHERE project_id = ? AND category = 'todo' "
        "ORDER BY position LIMIT 1",
        (project_id,),
    ).fetchone()
    return row[0] if row else None


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

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

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
        with Session(self._engine, expire_on_commit=False) as session:
            row = self._new_row(item)
            session.add(row)
            session.commit()
            return self._to_model(row)

    def get_by_id(self, item_id: UUID) -> M:
        """Get an entity by ID."""
        with Session(self._engine) as session:
            return self._to_model(self._get_row(session, item_id))

    def update(self, item_id: UUID, update: U) -> M:
        """Update an entity (partial update)."""
        with Session(self._engine, expire_on_commit=False) as session:
            row = self._get_row(session, item_id)
            for field, value in update.model_dump(exclude_unset=True).items():
                setattr(row, field, value)
            row.modified_at = utc_now()
            session.commit()
            return self._to_model(row)

    def replace(self, item_id: UUID, replace: R) -> M:
        """Replace an entity (full update), keeping its ID and created_at."""
        with Session(self._engine, expire_on_commit=False) as session:
            row = self._get_row(session, item_id)
            for field, value in replace.model_dump().items():
                setattr(row, field, value)
            row.modified_at = utc_now()
            session.commit()
            return self._to_model(row)

    def delete(self, item_id: UUID) -> None:
        """Delete an entity.

        Foreign keys (ON DELETE RESTRICT) block deleting rows that still have
        dependants; the service layer checks this first.
        """
        with Session(self._engine) as session:
            session.delete(self._get_row(session, item_id))
            session.commit()

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
        with Session(self._engine) as session:
            rows = session.scalars(stmt.offset(offset)).all()
            return [self._to_model(row) for row in rows]

    def _count(self, filters: dict[str, Any], search: str | None) -> int:
        stmt = select(func.count()).select_from(self._query(filters, search).subquery())
        with Session(self._engine) as session:
            return session.scalar(stmt) or 0


class SQLiteProjectBackend(
    ProjectSpec,
    SQLiteBackend[Project, ProjectCreate, ProjectUpdate, ProjectReplace],
):
    """SQLite project storage."""

    model_type = Project
    row_type = ProjectRow


class SQLiteBoardBackend(
    BoardSpec,
    SQLiteBackend[Board, BoardCreate, BoardUpdate, BoardReplace],
):
    """SQLite board storage."""

    model_type = Board
    row_type = BoardRow


class SQLiteStatusBackend(
    StatusSpec,
    SQLiteBackend[ProjectStatus, StatusCreate, StatusUpdate, StatusReplace],
):
    """SQLite status storage."""

    model_type = ProjectStatus
    row_type = StatusRow


class SQLiteWorkItemTypeBackend(
    WorkItemTypeSpec,
    SQLiteBackend[
        WorkItemType, WorkItemTypeCreate, WorkItemTypeUpdate, WorkItemTypeReplace
    ],
):
    """SQLite work item type storage."""

    model_type = WorkItemType
    row_type = WorkItemTypeRow


class SQLiteStatusTransitionBackend(
    StatusTransitionSpec,
    SQLiteBackend[
        StatusTransition,
        StatusTransitionCreate,
        StatusTransitionUpdate,
        StatusTransitionReplace,
    ],
):
    """SQLite status transition storage."""

    model_type = StatusTransition
    row_type = StatusTransitionRow


class SQLiteWorkItemBackend(
    WorkItemSpec,
    SQLiteBackend[WorkItem, WorkItemCreate, WorkItemUpdate, WorkItemReplace],
):
    """SQLite work item storage."""

    model_type = WorkItem
    row_type = WorkItemRow

    def _new_row(self, item: WorkItemCreate) -> WorkItemRow:
        return WorkItemRow(**new_work_item_fields(item))


class SQLiteFunctionBackend(
    FunctionSpec,
    SQLiteBackend[Function, FunctionCreate, FunctionUpdate, FunctionReplace],
):
    """SQLite function storage."""

    model_type = Function
    row_type = FunctionRow
