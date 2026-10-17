from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Uuid,
    false,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator):
    """Store datetimes as naive UTC and read them back as aware UTC.

    SQLite has no timezone type, so the offset would otherwise be lost.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=UTC)


class Base(DeclarativeBase):
    """Declarative base for the tables."""

    trashed: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false()
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    modified_at: Mapped[datetime] = mapped_column(UTCDateTime)


class ProjectRow(Base):
    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    labels: Mapped[list[str]] = mapped_column(JSON, default=list, server_default="[]")


class WorkItemRow(Base):
    __tablename__ = "work_items"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    project_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    type_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("work_item_types.id", ondelete="RESTRICT"), nullable=False
    )
    status_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("statuses.id", ondelete="RESTRICT"), nullable=False
    )
    parent_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("work_items.id", ondelete="RESTRICT"), nullable=True
    )
    labels: Mapped[list[str]] = mapped_column(JSON, default=list, server_default="[]")


class BoardRow(Base):
    __tablename__ = "boards"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    filter: Mapped[str | None] = mapped_column(String, nullable=True)
    project_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    labels: Mapped[list[str]] = mapped_column(JSON, default=list, server_default="[]")


class WorkItemTypeRow(Base):
    __tablename__ = "work_item_types"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    project_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String)
    level: Mapped[str] = mapped_column(String)
    position: Mapped[int] = mapped_column(Integer)


class StatusRow(Base):
    __tablename__ = "statuses"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    project_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    position: Mapped[int] = mapped_column(Integer)


class StatusTransitionRow(Base):
    __tablename__ = "status_transitions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    project_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    from_status_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("statuses.id", ondelete="CASCADE"), nullable=False
    )
    to_status_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("statuses.id", ondelete="CASCADE"), nullable=False
    )


class FunctionRow(Base):
    __tablename__ = "functions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    code: Mapped[str] = mapped_column(String)
    labels: Mapped[list[str]] = mapped_column(JSON, default=list, server_default="[]")
