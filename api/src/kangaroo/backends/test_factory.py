import pytest

from kangaroo.backends import Backends, create_backends
from kangaroo.backends.sqlite import (
    SQLiteBoardBackend,
    SQLiteFunctionBackend,
    SQLiteProjectBackend,
    SQLiteStatusBackend,
    SQLiteStatusTransitionBackend,
    SQLiteWorkItemBackend,
    SQLiteWorkItemTypeBackend,
)
from kangaroo.schemas import ProjectCreate
from kangaroo.settings import Settings


def test_sqlite_url_selects_sqlite_backends():
    backends = create_backends("sqlite://memory")
    assert isinstance(backends, Backends)
    assert isinstance(backends.functions, SQLiteFunctionBackend)
    assert isinstance(backends.work_items, SQLiteWorkItemBackend)
    assert isinstance(backends.projects, SQLiteProjectBackend)
    assert isinstance(backends.boards, SQLiteBoardBackend)
    assert isinstance(backends.statuses, SQLiteStatusBackend)
    assert isinstance(backends.types, SQLiteWorkItemTypeBackend)
    assert isinstance(backends.transitions, SQLiteStatusTransitionBackend)


def test_backends_share_one_database():
    backends = create_backends("sqlite://memory")
    project = backends.projects.create(ProjectCreate(name="Shared"))
    assert backends.projects.get_by_id(project.id) == project
    assert backends.functions.list_all() == []


@pytest.mark.parametrize(
    "url", ["memory://", "postgresql://localhost/kangaroo", "sqlite-typo://x"]
)
def test_unsupported_url_raises(url):
    with pytest.raises(ValueError, match="Unsupported DATABASE_URL"):
        create_backends(url)


def test_database_url_defaults_to_sqlite_memory(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert Settings(_env_file=None).database_url == "sqlite://memory"


def test_database_url_read_from_env_file(monkeypatch, tmp_path):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("DATABASE_URL=sqlite:///kangaroo.db\n")
    assert Settings(_env_file=env_file).database_url == "sqlite:///kangaroo.db"


def test_database_url_read_from_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite://memory")
    assert Settings().database_url == "sqlite://memory"
