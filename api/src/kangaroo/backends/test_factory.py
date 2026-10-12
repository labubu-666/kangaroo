import pytest

from kangaroo.backends.factory import create_backends
from kangaroo.backends.memory import (
    InMemoryBoardBackend,
    InMemoryFunctionBackend,
    InMemoryProjectBackend,
    InMemoryStatusBackend,
    InMemoryStatusTransitionBackend,
    InMemoryWorkItemBackend,
    InMemoryWorkItemTypeBackend,
)
from kangaroo.backends.sqlite import (
    SQLiteBoardBackend,
    SQLiteFunctionBackend,
    SQLiteProjectBackend,
    SQLiteStatusBackend,
    SQLiteStatusTransitionBackend,
    SQLiteWorkItemBackend,
    SQLiteWorkItemTypeBackend,
)
from kangaroo.settings import Settings


def test_memory_url_selects_memory_backends():
    work_items, projects, boards, statuses, types, transitions, functions = (
        create_backends("memory://")
    )
    assert isinstance(functions, InMemoryFunctionBackend)
    assert isinstance(work_items, InMemoryWorkItemBackend)
    assert isinstance(projects, InMemoryProjectBackend)
    assert isinstance(boards, InMemoryBoardBackend)
    assert isinstance(statuses, InMemoryStatusBackend)
    assert isinstance(types, InMemoryWorkItemTypeBackend)
    assert isinstance(transitions, InMemoryStatusTransitionBackend)


def test_sqlite_url_selects_sqlite_backends():
    work_items, projects, boards, statuses, types, transitions, functions = (
        create_backends("sqlite://memory")
    )
    assert isinstance(functions, SQLiteFunctionBackend)
    assert isinstance(work_items, SQLiteWorkItemBackend)
    assert isinstance(projects, SQLiteProjectBackend)
    assert isinstance(boards, SQLiteBoardBackend)
    assert isinstance(statuses, SQLiteStatusBackend)
    assert isinstance(types, SQLiteWorkItemTypeBackend)
    assert isinstance(transitions, SQLiteStatusTransitionBackend)


def test_unsupported_url_raises():
    with pytest.raises(ValueError, match="Unsupported DATABASE_URL"):
        create_backends("postgresql://localhost/kangaroo")


def test_database_url_defaults_to_memory(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert Settings(_env_file=None).database_url == "memory://"


def test_database_url_read_from_env_file(monkeypatch, tmp_path):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("DATABASE_URL=sqlite:///kangaroo.db\n")
    assert Settings(_env_file=env_file).database_url == "sqlite:///kangaroo.db"


def test_database_url_read_from_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite://memory")
    assert Settings().database_url == "sqlite://memory"
