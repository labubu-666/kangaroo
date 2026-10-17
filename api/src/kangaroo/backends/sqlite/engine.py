from sqlalchemy import (
    Engine,
    create_engine,
    event,
)
from sqlalchemy.pool import StaticPool

from kangaroo.backends.sqlite.migrations import (
    _add_missing_labels_column,
    _migrate_to_project_templates,
)
from kangaroo.backends.sqlite.tables import Base


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
