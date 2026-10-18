from sqlalchemy import (
    Engine,
    create_engine,
    event,
)
from sqlalchemy.pool import StaticPool

from kangaroo.repositories.tables import Base


def create_engine_for(url: str) -> Engine:
    """Create a SQLAlchemy engine with foreign keys enabled and the schema ready.

    ``sqlite://memory`` maps to a shared in-memory database. ``sqlite:///path.db``
    is a file database. Any other URL is rejected, so a typo cannot quietly give
    a database that is lost on restart.

    Raises:
        ValueError: If the URL is not ``sqlite://memory`` or a ``sqlite:///`` file URL.
    """
    is_file = url.startswith("sqlite:///") and len(url) > len("sqlite:///")
    if url != "sqlite://memory" and not is_file:
        raise ValueError(
            f"Unsupported DATABASE_URL: {url!r}. Use sqlite://memory or "
            "sqlite:///path/to/file.db"
        )
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
    return engine
