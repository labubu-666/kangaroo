from sqlalchemy import Engine, create_engine

from kangaroo.repositories.tables import Base


def create_engine_for(url: str) -> Engine:
    """Create a PostgreSQL engine and create any missing tables.

    Only PostgreSQL URLs are accepted, so a typo cannot quietly point the app at
    another database. ``postgresql://`` is normalised to the psycopg driver.

    Raises:
        ValueError: If the URL is not a PostgreSQL URL. The URL is not echoed,
            because it contains the password.
    """
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url.removeprefix("postgresql://")
    if not url.startswith("postgresql+psycopg://"):
        raise ValueError(
            "Unsupported DATABASE_URL. Use postgresql+psycopg://user:password@host/database"
        )
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    return engine
