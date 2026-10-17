import sqlite3
from uuid import UUID

import pytest
from sqlalchemy import inspect

from kangaroo.backends.sqlite import (
    SQLiteProjectBackend,
    SQLiteStatusBackend,
    SQLiteWorkItemBackend,
    SQLiteWorkItemTypeBackend,
    create_sqlite_engine,
)
from kangaroo.backends.sqlite import migrations as sqlite_module
from kangaroo.filters import parse_filter
from kangaroo.schemas import ProjectCreate

OLD_SCHEMA = """
CREATE TABLE projects (
id CHAR(32) NOT NULL,
name VARCHAR NOT NULL,
description VARCHAR,
created_at DATETIME NOT NULL, trashed BOOLEAN NOT NULL DEFAULT 0, modified_at DATETIME, labels JSON NOT NULL DEFAULT '[]',
PRIMARY KEY (id)
);
CREATE TABLE boards (
    id CHAR(32) NOT NULL,
    name VARCHAR NOT NULL,
    description VARCHAR,
    filter VARCHAR,
    project_id CHAR(32) NOT NULL REFERENCES projects (id) ON DELETE RESTRICT,
    created_at DATETIME NOT NULL,
    trashed BOOLEAN NOT NULL DEFAULT 0, modified_at DATETIME, labels JSON NOT NULL DEFAULT '[]',
    PRIMARY KEY (id)
);
CREATE TABLE work_items (
id CHAR(32) NOT NULL,
title VARCHAR NOT NULL,
description VARCHAR,
project_id CHAR(32) NOT NULL,
type VARCHAR NOT NULL,
parent_id CHAR(32),
status VARCHAR NOT NULL,
created_at DATETIME NOT NULL, trashed BOOLEAN NOT NULL DEFAULT 0, modified_at DATETIME, labels JSON NOT NULL DEFAULT '[]',
PRIMARY KEY (id),
FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE RESTRICT,
FOREIGN KEY(parent_id) REFERENCES work_items (id) ON DELETE RESTRICT
);
"""

NOW = "2026-01-01 10:00:00"

IDS = {
    "p1": "0190a000000070008000000000000001",
    "b1": "0190a000000070008000000000000002",
    "t1": "0190a000000070008000000000000011",
    "t2": "0190a000000070008000000000000012",
    "t3": "0190a000000070008000000000000013",
    "s1": "0190a000000070008000000000000014",
    "x": "0190a000000070008000000000000015",
}


def _id(name):
    return IDS[name]


def _old_database(path, items):
    """Write a database with the pre-template schema and the given work items.

    ``items`` is a list of (id, title, project_id, type, parent_id, status), using
    the readable names in ``IDS``.
    """
    conn = sqlite3.connect(path)
    conn.executescript(OLD_SCHEMA)
    conn.execute(
        "INSERT INTO projects (id, name, created_at, labels) VALUES (?, ?, ?, '[]')",
        (_id("p1"), "Alpha", NOW),
    )
    conn.execute(
        "INSERT INTO boards (id, name, project_id, filter, created_at, labels) "
        "VALUES (?, 'Board', ?, \"status == 'in_progress'\", ?, '[]')",
        (_id("b1"), _id("p1"), NOW),
    )
    for item_id, title, project_id, kind, parent_id, status in items:
        conn.execute(
            "INSERT INTO work_items (id, title, project_id, type, parent_id, status, "
            "created_at, modified_at, trashed, labels) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, '[]')",
            (
                _id(item_id),
                title,
                _id(project_id),
                kind,
                _id(parent_id) if parent_id else None,
                status,
                NOW,
                NOW,
            ),
        )
    conn.commit()
    conn.close()


@pytest.fixture
def old_db(tmp_path):
    """An old-schema database with a task, a subtask and an in-progress task."""
    path = tmp_path / "kangaroo.db"
    _old_database(
        path,
        [
            ("t1", "Open task", "p1", "task", None, "open"),
            ("t2", "Busy task", "p1", "task", None, "in_progress"),
            ("t3", "Done task", "p1", "task", None, "done"),
            ("s1", "Child", "p1", "subtask", "t2", "open"),
        ],
    )
    return path


def _open(path):
    return create_sqlite_engine(f"sqlite:///{path}")


def test_upgrade_keeps_every_work_item(old_db):
    engine = _open(old_db)
    items = SQLiteWorkItemBackend(engine).list_all()
    assert sorted(i.title for i in items) == [
        "Busy task",
        "Child",
        "Done task",
        "Open task",
    ]


def test_upgrade_maps_statuses_and_types_by_name(old_db):
    engine = _open(old_db)
    statuses = {
        s.name: s.id
        for s in SQLiteStatusBackend(engine).list_all(project_id=UUID(_id("p1")))
    }
    types = {
        t.name: t
        for t in SQLiteWorkItemTypeBackend(engine).list_all(project_id=UUID(_id("p1")))
    }
    items = {i.title: i for i in SQLiteWorkItemBackend(engine).list_all()}

    assert items["Open task"].status_id == statuses["Open"]
    assert items["Busy task"].status_id == statuses["In Progress"]
    assert items["Done task"].status_id == statuses["Done"]
    assert items["Open task"].type_id == types["Task"].id
    assert items["Child"].type_id == types["Subtask"].id
    assert types["Subtask"].level == "subtask"


def test_upgrade_keeps_parent_links(old_db):
    engine = _open(old_db)
    items = {i.title: i for i in SQLiteWorkItemBackend(engine).list_all()}
    assert items["Child"].parent_id == items["Busy task"].id


def test_upgrade_creates_statuses_for_each_project(old_db):
    engine = _open(old_db)
    statuses = SQLiteStatusBackend(engine).list_all(project_id=UUID(_id("p1")))
    assert sorted(s.name for s in statuses) == ["Done", "In Progress", "Open"]


def test_saved_filter_matches_same_items_after_upgrade(old_db):
    """A board filter written against the old values still finds the same items."""
    engine = _open(old_db)
    work_items = SQLiteWorkItemBackend(engine)
    statuses = {s.id: s for s in SQLiteStatusBackend(engine).list_all()}
    types = {t.id: t for t in SQLiteWorkItemTypeBackend(engine).list_all()}

    def record(item):
        status = statuses[item.status_id]
        kind = types[item.type_id]
        return {
            "title": item.title,
            "description": item.description,
            "status": status.name,
            "status_id": str(item.status_id),
            "statusCategory": status.category,
            "type": kind.name,
            "type_id": str(item.type_id),
            "typeLevel": kind.level,
            "parent_id": str(item.parent_id) if item.parent_id else None,
            "project.id": str(item.project_id),
            "project.name": "Alpha",
            "labels": item.labels,
            "trashed": "true" if item.trashed else "false",
        }

    matched = {
        i.title
        for i in work_items.list_all()
        if parse_filter("status == 'in_progress'")(record(i))
    }
    assert matched == {"Busy task"}
    assert {
        i.title
        for i in work_items.list_all()
        if parse_filter("status == 'open' or type == 'Subtask'")(record(i))
    } == {"Open task", "Child"}


def test_upgrade_is_idempotent(old_db):
    _open(old_db).dispose()
    before = (
        sqlite3.connect(old_db)
        .execute("SELECT id, status_id, type_id FROM work_items ORDER BY id")
        .fetchall()
    )
    engine = _open(old_db)
    after = (
        sqlite3.connect(old_db)
        .execute("SELECT id, status_id, type_id FROM work_items ORDER BY id")
        .fetchall()
    )
    assert before == after
    assert len(SQLiteStatusBackend(engine).list_all()) == 3


def test_upgrade_leaves_no_dangling_references(old_db):
    _open(old_db)
    conn = sqlite3.connect(old_db)
    assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    conn.close()


def test_upgrade_writes_a_backup_first(old_db):
    _open(old_db)
    backups = list(old_db.parent.glob("kangaroo.db.pre-project-templates-*.bak"))
    assert len(backups) == 1
    conn = sqlite3.connect(backups[0])
    assert conn.execute("SELECT COUNT(*) FROM work_items").fetchone()[0] == 4
    assert "status" in {
        c[1] for c in conn.execute("PRAGMA table_info(work_items)").fetchall()
    }
    conn.close()


def test_no_backup_when_upgrade_does_not_run(old_db):
    _open(old_db).dispose()
    _open(old_db).dispose()
    backups = list(old_db.parent.glob("kangaroo.db.pre-project-templates-*.bak"))
    assert len(backups) == 1


def test_in_memory_database_skips_backup(monkeypatch):
    called = []
    monkeypatch.setattr(sqlite_module, "_backup_database", lambda *a: called.append(a))
    create_sqlite_engine("sqlite://memory")
    assert called == []


def test_failed_backup_stops_the_upgrade(old_db, monkeypatch):
    def broken(engine, path):
        raise sqlite3.OperationalError("disk full")

    monkeypatch.setattr(sqlite_module, "_backup_database", broken)
    with pytest.raises(sqlite3.OperationalError, match="disk full"):
        _open(old_db)
    conn = sqlite3.connect(old_db)
    columns = {c[1] for c in conn.execute("PRAGMA table_info(work_items)")}
    conn.close()
    assert "status" in columns
    assert "status_id" not in columns


def test_failed_foreign_key_check_rolls_back(old_db, monkeypatch):
    """If the rebuilt data breaks a foreign key, nothing is changed."""
    real_rebuild = sqlite_module._rebuild_work_items

    def rebuild_then_break(cursor):
        real_rebuild(cursor)
        cursor.execute(
            "UPDATE work_items SET project_id = 'missing' WHERE id = ?", (IDS["t1"],)
        )

    monkeypatch.setattr(sqlite_module, "_rebuild_work_items", rebuild_then_break)
    with pytest.raises(RuntimeError, match="Foreign key check failed"):
        _open(old_db)
    conn = sqlite3.connect(old_db)
    columns = {c[1] for c in conn.execute("PRAGMA table_info(work_items)")}
    count = conn.execute("SELECT COUNT(*) FROM work_items").fetchone()[0]
    conn.close()
    assert "status" in columns
    assert count == 4


def test_unknown_status_moves_to_first_todo_with_warning(tmp_path, caplog):
    path = tmp_path / "kangaroo.db"
    _old_database(path, [("x", "Weird", "p1", "task", None, "blocked")])
    with caplog.at_level("WARNING"):
        engine = _open(path)
    item = SQLiteWorkItemBackend(engine).get_by_id(_id_of(engine, "Weird"))
    statuses = {s.id: s.name for s in SQLiteStatusBackend(engine).list_all()}
    assert statuses[item.status_id] == "Open"
    assert "blocked" in caplog.text


def _id_of(engine, title):
    return next(
        i.id for i in SQLiteWorkItemBackend(engine).list_all() if i.title == title
    )


def test_new_database_needs_no_upgrade(tmp_path):
    path = tmp_path / "fresh.db"
    engine = _open(path)
    project = SQLiteProjectBackend(engine).create(ProjectCreate(name="Fresh"))
    assert project.id is not None
    assert not list(tmp_path.glob("*.bak"))
    assert "status_id" in {c["name"] for c in inspect(engine).get_columns("work_items")}
