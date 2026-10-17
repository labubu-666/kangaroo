import logging
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid7

from sqlalchemy import (
    Engine,
    inspect,
)

from kangaroo.backends.base import (
    utc_now,
)
from kangaroo.templates import TO_DO_LIST


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
            OLD_TYPE_NAMES.get(old_type),
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
