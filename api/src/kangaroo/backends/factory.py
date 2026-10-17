from dataclasses import dataclass

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from kangaroo.backends.base import (
    BoardBackend,
    FunctionBackend,
    ProjectBackend,
    StatusBackend,
    StatusTransitionBackend,
    WorkItemBackend,
    WorkItemTypeBackend,
)
from kangaroo.backends.sqlite import (
    SQLiteBoardBackend,
    SQLiteFunctionBackend,
    SQLiteProjectBackend,
    SQLiteStatusBackend,
    SQLiteStatusTransitionBackend,
    SQLiteWorkItemBackend,
    SQLiteWorkItemTypeBackend,
    create_sqlite_engine,
)


@dataclass(frozen=True)
class Backends:
    """Every storage backend the app uses, all sharing one database."""

    work_items: WorkItemBackend
    projects: ProjectBackend
    boards: BoardBackend
    statuses: StatusBackend
    types: WorkItemTypeBackend
    transitions: StatusTransitionBackend
    functions: FunctionBackend
    engine: Engine

    def bound(self, session: Session) -> Backends:
        """Copies of every backend that all run inside ``session``."""
        return Backends(
            work_items=self.work_items.bind(session),
            projects=self.projects.bind(session),
            boards=self.boards.bind(session),
            statuses=self.statuses.bind(session),
            types=self.types.bind(session),
            transitions=self.transitions.bind(session),
            functions=self.functions.bind(session),
            engine=self.engine,
        )


def create_backends(database_url: str) -> Backends:
    """Build every backend for a DATABASE_URL.

    ``sqlite://...`` selects the SQLite backends, which share one engine.
    ``sqlite://memory`` is a shared in-memory database.

    Raises:
        ValueError: If the URL is not supported.
    """
    if not database_url.startswith("sqlite://"):
        raise ValueError(f"Unsupported DATABASE_URL: {database_url}")
    engine = create_sqlite_engine(database_url)
    return Backends(
        work_items=SQLiteWorkItemBackend(engine),
        projects=SQLiteProjectBackend(engine),
        boards=SQLiteBoardBackend(engine),
        statuses=SQLiteStatusBackend(engine),
        types=SQLiteWorkItemTypeBackend(engine),
        transitions=SQLiteStatusTransitionBackend(engine),
        functions=SQLiteFunctionBackend(engine),
        engine=engine,
    )
