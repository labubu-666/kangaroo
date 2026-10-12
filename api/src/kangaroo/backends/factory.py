from kangaroo.backends.base import (
    BoardBackend,
    FunctionBackend,
    ProjectBackend,
    StatusBackend,
    StatusTransitionBackend,
    WorkItemBackend,
    WorkItemTypeBackend,
)
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
    create_sqlite_engine,
)


def create_backends(
    database_url: str,
) -> tuple[
    WorkItemBackend,
    ProjectBackend,
    BoardBackend,
    StatusBackend,
    WorkItemTypeBackend,
    StatusTransitionBackend,
    FunctionBackend,
]:
    """Build every backend for a DATABASE_URL.

    Returns the work item, project, board, status, work item type, status
    transition and function backends, in that order. ``memory://`` selects the
    in-memory backends. ``sqlite://...`` selects the SQLite backends, which share
    one engine.

    Raises:
        ValueError: If the URL is not supported.
    """
    if database_url == "memory://":
        return (
            InMemoryWorkItemBackend(),
            InMemoryProjectBackend(),
            InMemoryBoardBackend(),
            InMemoryStatusBackend(),
            InMemoryWorkItemTypeBackend(),
            InMemoryStatusTransitionBackend(),
            InMemoryFunctionBackend(),
        )
    if database_url.startswith("sqlite://"):
        engine = create_sqlite_engine(database_url)
        return (
            SQLiteWorkItemBackend(engine),
            SQLiteProjectBackend(engine),
            SQLiteBoardBackend(engine),
            SQLiteStatusBackend(engine),
            SQLiteWorkItemTypeBackend(engine),
            SQLiteStatusTransitionBackend(engine),
            SQLiteFunctionBackend(engine),
        )
    raise ValueError(f"Unsupported DATABASE_URL: {database_url}")
