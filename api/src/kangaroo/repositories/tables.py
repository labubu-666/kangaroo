from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    false,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, validates
from sqlalchemy.types import TypeDecorator

from kangaroo.utils import markdown_to_plain


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

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, sort_order=-1)
    trashed: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false()
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    modified_at: Mapped[datetime] = mapped_column(UTCDateTime)


class ProjectRow(Base):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    labels: Mapped[list[str]] = mapped_column(JSON, default=list, server_default="[]")


class WorkItemRow(Base):
    __tablename__ = "work_items"

    summary: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    plain_description: Mapped[str | None] = mapped_column(
        String, nullable=True, info={"derived_from": "description"}
    )
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
    due_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

    @validates("description")
    def _sync_plain_description(self, _key, value):
        self.plain_description = markdown_to_plain(value)
        return value


class BoardRow(Base):
    __tablename__ = "boards"

    name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    filter: Mapped[str | None] = mapped_column(String, nullable=True)
    project_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False
    )
    labels: Mapped[list[str]] = mapped_column(JSON, default=list, server_default="[]")
    status_order: Mapped[list[str]] = mapped_column(
        JSON, default=list, server_default="[]"
    )
    hidden_status_ids: Mapped[list[str]] = mapped_column(
        JSON, default=list, server_default="[]"
    )


class WorkItemTypeRow(Base):
    __tablename__ = "work_item_types"

    project_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String)
    position: Mapped[int] = mapped_column(Integer)


class StatusRow(Base):
    __tablename__ = "statuses"

    project_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    position: Mapped[int] = mapped_column(Integer)


class StatusTransitionRow(Base):
    __tablename__ = "status_transitions"

    project_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    from_status_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("statuses.id", ondelete="CASCADE"), nullable=False
    )
    to_status_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("statuses.id", ondelete="CASCADE"), nullable=False
    )


class InvocationRow(Base):
    __tablename__ = "invocations"

    function_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("functions.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String)
    logs: Mapped[str] = mapped_column(String)
    result: Mapped[Any] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(String, nullable=True)


class FunctionRow(Base):
    __tablename__ = "functions"

    name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    code: Mapped[str] = mapped_column(String)
    labels: Mapped[list[str]] = mapped_column(JSON, default=list, server_default="[]")


class KnowledgeBaseRow(Base):
    __tablename__ = "knowledge_bases"

    name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    labels: Mapped[list[str]] = mapped_column(JSON, default=list, server_default="[]")


class ArticleRow(Base):
    __tablename__ = "articles"

    knowledge_base_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("knowledge_bases.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(String)
    body: Mapped[str | None] = mapped_column(String, nullable=True)
    plain_body: Mapped[str | None] = mapped_column(
        String, nullable=True, info={"derived_from": "body"}
    )
    labels: Mapped[list[str]] = mapped_column(JSON, default=list, server_default="[]")
    viewed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

    @validates("body")
    def _sync_plain_body(self, _key, value):
        self.plain_body = markdown_to_plain(value)
        return value


class ApiKeyRow(Base):
    """A machine login. Only the SHA-256 hash of the key is stored, never the key."""

    __tablename__ = "api_keys"

    name: Mapped[str] = mapped_column(String)
    key_hash: Mapped[str] = mapped_column(String, unique=True, index=True)
    owner: Mapped[str] = mapped_column(String, index=True)
    owner_email: Mapped[str | None] = mapped_column(String, nullable=True)
    owner_name: Mapped[str | None] = mapped_column(String, nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)


class RecentHistoryRow(Base):
    """One item a user has opened recently. A repeat visit updates the same row."""

    __tablename__ = "recent_history"
    __table_args__ = (UniqueConstraint("owner", "type", "item_id"),)

    owner: Mapped[str] = mapped_column(String, index=True)
    type: Mapped[str] = mapped_column(String)
    item_id: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    parent: Mapped[str | None] = mapped_column(String, nullable=True)
    to: Mapped[str] = mapped_column(String)
    params: Mapped[dict[str, str]] = mapped_column(JSON)
    search: Mapped[dict[str, str]] = mapped_column(
        JSON, default=dict, server_default="{}"
    )


class PipelineRow(Base):
    """A saved pipeline: a named graph of functions that reference each other."""

    __tablename__ = "pipelines"

    name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    steps: Mapped[dict[str, Any]] = mapped_column(JSON)
    labels: Mapped[list[str]] = mapped_column(JSON, default=list, server_default="[]")


class PipelineRunRow(Base):
    """One run of a pipeline. Its status is PENDING, RUNNING, SUCCESS or FAILURE."""

    __tablename__ = "pipeline_runs"

    pipeline_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String)
    # The user claims that started the run. Steps mint their token for this user.
    started_by: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class PipelineStepRow(Base):
    """One step of a run. The orchestrator claims PENDING steps from this table."""

    __tablename__ = "pipeline_steps"

    pipeline_run_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("pipeline_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, index=True)
    invocation_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("invocations.id", ondelete="SET NULL"), nullable=True
    )
    started_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
