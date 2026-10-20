import os

# The app reads DATABASE_URL when its engine is first used. Point it at an
# in-memory database before any test runs.
os.environ["DATABASE_URL"] = "sqlite://memory"

from collections.abc import Iterator

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from kangaroo.app import app
from kangaroo.repositories import (
    ArticleRepository,
    BoardRepository,
    FunctionRepository,
    InvocationRepository,
    ProjectRepository,
    StatusRepository,
    StatusTransitionRepository,
    WorkItemRepository,
    WorkItemTypeRepository,
    create_engine_for,
)
from kangaroo.routes.auth import require_user


@pytest.fixture(autouse=True)
def signed_in_user() -> Iterator[None]:
    """Every test runs as a logged-in user. Auth tests opt out themselves."""
    app.dependency_overrides[require_user] = lambda: {"email": "test@example.com"}
    yield
    app.dependency_overrides.pop(require_user, None)


@pytest.fixture
def engine() -> Engine:
    """A fresh, empty in-memory database for each test."""
    return create_engine_for("sqlite://memory")


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
def articles(session):
    return ArticleRepository(session)
