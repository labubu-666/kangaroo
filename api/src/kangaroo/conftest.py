import os

# The app reads DATABASE_URL when its engine is first used. Tests replace the
# engine through get_engine, so this value only has to be a valid URL.
os.environ["DATABASE_URL"] = "postgresql+psycopg://unused@localhost/unused"

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from pytest_testcontainers import make_postgres
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from kangaroo.app import app
from kangaroo.repositories import (
    ArticleRepository,
    BoardRepository,
    FunctionRepository,
    InvocationRepository,
    KnowledgeBaseRepository,
    ProjectRepository,
    StatusRepository,
    StatusTransitionRepository,
    WorkItemRepository,
    WorkItemTypeRepository,
    create_engine_for,
)
from kangaroo.repositories.tables import Base
from kangaroo.routes.auth import require_user
from kangaroo.routes.dependencies import get_engine
from kangaroo.testing import seed_project


@pytest.fixture(autouse=True)
def signed_in_user(monkeypatch) -> None:
    """Every test runs as a logged-in user. Auth tests opt out with ``logged_out``."""
    monkeypatch.setitem(
        app.dependency_overrides, require_user, lambda: {"email": "test@example.com"}
    )


@pytest.fixture
def logged_out(monkeypatch) -> None:
    """Drop the logged-in user so requests go through real authentication."""
    monkeypatch.delitem(app.dependency_overrides, require_user)


@pytest.fixture(scope="session")
def pg_18():
    """One PostgreSQL 18 container for the whole test run."""
    with make_postgres(image="postgres:18.7-alpine") as pg:
        yield pg


@pytest.fixture(scope="session")
def database_engine(pg_18) -> Iterator[Engine]:
    """One engine for the whole run, with the schema created once."""
    engine = create_engine_for(pg_18.get_connection_url(driver="psycopg"))
    yield engine
    engine.dispose()


@pytest.fixture
def engine(database_engine) -> Engine:
    """Empty tables for each test. A test that fails leaves its rows for inspection."""
    tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
    with database_engine.begin() as connection:
        connection.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    return database_engine


@pytest.fixture
def client(engine, monkeypatch) -> TestClient:
    """A TestClient whose requests use this test's database."""
    monkeypatch.setitem(app.dependency_overrides, get_engine, lambda: engine)
    return TestClient(app)


@pytest.fixture
def session(engine) -> Iterator[Session]:
    """One session for the test; every repository in the test shares it."""
    with Session(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
def projects(session):
    return ProjectRepository(session)


@pytest.fixture
def work_items(session):
    return WorkItemRepository(session)


@pytest.fixture
def boards(session):
    return BoardRepository(session)


@pytest.fixture
def statuses(session):
    return StatusRepository(session)


@pytest.fixture
def types(session):
    return WorkItemTypeRepository(session)


@pytest.fixture
def transitions(session):
    return StatusTransitionRepository(session)


@pytest.fixture
def functions(session):
    return FunctionRepository(session)


@pytest.fixture
def invocations(session):
    return InvocationRepository(session)


@pytest.fixture
def knowledge_bases(session):
    return KnowledgeBaseRepository(session)


@pytest.fixture
def articles(session):
    return ArticleRepository(session)


@pytest.fixture
def seeded(projects, statuses, types):
    """A project with the To Do List statuses and types."""
    return seed_project(projects, statuses, types)
