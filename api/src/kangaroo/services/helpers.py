from collections.abc import Callable
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from kangaroo.errors import (
    InvalidReferenceError,
    NotFoundError,
)
from kangaroo.filters import parse_filter
from kangaroo.repositories import (
    KnowledgeBaseRepository,
    ProjectRepository,
    StatusRepository,
    WorkItemTypeRepository,
)
from kangaroo.repositories.repositories import Repository, clean_search
from kangaroo.schemas import (
    ProjectStatus,
    SearchHit,
    StatusCreate,
    StatusRef,
    StatusReplace,
    TypeRef,
    WorkItem,
    WorkItemDetail,
    WorkItemListItem,
    WorkItemType,
    WorkItemTypeCreate,
    WorkItemTypeReplace,
)
from kangaroo.utils import snippet_around


def ensure_project_exists(projects: ProjectRepository, project_id: UUID | None) -> None:
    """Raise InvalidReferenceError if the project is null or does not exist."""
    if project_id is None:
        raise InvalidReferenceError("project_id cannot be null")
    try:
        projects.get_by_id(project_id)
    except NotFoundError:
        raise InvalidReferenceError("Project not found") from None


def ensure_knowledge_base_exists(
    knowledge_bases: KnowledgeBaseRepository, knowledge_base_id: UUID
) -> None:
    """Raise InvalidReferenceError if the knowledge base does not exist."""
    try:
        knowledge_bases.get_by_id(knowledge_base_id)
    except NotFoundError:
        raise InvalidReferenceError("Knowledge base not found") from None


def in_due_range(
    due_at: datetime | None, due_from: datetime | None, due_to: datetime | None
) -> bool:
    """Whether ``due_at`` is in [due_from, due_to). Items without a due date never are."""
    if due_from is None and due_to is None:
        return True
    if due_at is None:
        return False
    return (due_from is None or due_at >= due_from) and (
        due_to is None or due_at < due_to
    )


def project_names(projects: ProjectRepository) -> dict[UUID, str]:
    return {project.id: project.name for project in projects.list_all()}


FILTER_KEYS = (
    "summary",
    "description",
    "status",
    "status_id",
    "statusCategory",
    "type",
    "type_id",
    "parent_id",
    "project.id",
    "project.name",
    "labels",
    "trashed",
)


def make_record(values: dict[str, Any]) -> dict[str, Any]:
    """Return a filter record with every key in FILTER_KEYS; unset keys are None."""
    return {key: values.get(key) for key in FILTER_KEYS}


def filter_record(
    item: WorkItem,
    project_names: dict[UUID, str],
    statuses: dict[UUID, ProjectStatus],
    types: dict[UUID, WorkItemType],
) -> dict[str, Any]:
    """Flatten a work item into the record that filter predicates read."""
    status = statuses.get(item.status_id)
    work_item_type = types.get(item.type_id)
    return make_record(
        {
            "summary": item.summary,
            "description": item.description,
            "status": status.name if status else None,
            "status_id": str(item.status_id),
            "statusCategory": status.category if status else None,
            "type": work_item_type.name if work_item_type else None,
            "type_id": str(item.type_id),
            "parent_id": str(item.parent_id) if item.parent_id else None,
            "project.id": str(item.project_id),
            "project.name": project_names.get(item.project_id),
            "labels": item.labels,
            "trashed": "true" if item.trashed else "false",
        }
    )


def lookups(
    statuses: StatusRepository, types: WorkItemTypeRepository
) -> tuple[dict[UUID, ProjectStatus], dict[UUID, WorkItemType]]:
    return (
        {status.id: status for status in statuses.list_all()},
        {work_item_type.id: work_item_type for work_item_type in types.list_all()},
    )


def search_hit(plain: str | None, search: str | None) -> SearchHit | None:
    """The snippet for a search term, or None when there is no term or no match."""
    term = clean_search(search)
    found = snippet_around(plain, term) if term else None
    return SearchHit(text=found[0], match_count=found[1]) if found else None


def detail(
    item: WorkItem,
    statuses: dict[UUID, ProjectStatus],
    types: dict[UUID, WorkItemType],
) -> WorkItemDetail:
    status = statuses[item.status_id]
    work_item_type = types[item.type_id]
    return WorkItemDetail(
        **item.model_dump(exclude={"rendered_description"}),
        status=StatusRef(id=status.id, name=status.name, category=status.category),
        type=TypeRef(id=work_item_type.id, name=work_item_type.name),
    )


def list_item(
    item: WorkItem,
    statuses: dict[UUID, ProjectStatus],
    types: dict[UUID, WorkItemType],
    search: str | None,
) -> WorkItemListItem:
    return WorkItemListItem(
        **detail(item, statuses, types).model_dump(exclude={"rendered_description"}),
        snippet=search_hit(item.plain_description, search),
    )


def next_position(repository: Repository, project_id: UUID) -> int:
    """Place a new item after the last position already used in the project."""
    positions = [item.position for item in repository.list_all(project_id=project_id)]
    return max(positions, default=-1) + 1


def with_default_position[M: (StatusCreate, WorkItemTypeCreate)](
    repository: Repository, item: M, project_id: UUID
) -> M:
    """Place a new status or type last in its project when it has no position."""
    if item.position is not None:
        return item
    return item.model_copy(update={"position": next_position(repository, project_id)})


def keep_position[M: (StatusReplace, WorkItemTypeReplace)](
    current_position: int, replace: M
) -> M:
    """Keep the current position when a replace request leaves it out."""
    if replace.position is not None:
        return replace
    return replace.model_copy(update={"position": current_position})


def in_position_order[M: (ProjectStatus, WorkItemType)](items: list[M]) -> list[M]:
    """Sort by position. Items that share a position keep their creation order."""
    return sorted(items, key=lambda item: item.position)


def get_in_project[M: (ProjectStatus, WorkItemType)](
    repository: Repository, item_id: UUID, project_id: UUID, label: str
) -> M:
    """Return the item, raising InvalidReferenceError if it is missing or in another project."""
    try:
        item = repository.get_by_id(item_id)
    except NotFoundError:
        raise InvalidReferenceError(f"{label} not found") from None
    if item.project_id != project_id:
        raise InvalidReferenceError(f"{label} is not in the project")
    return item


def matches_search(item: BaseModel, text: str, fields: tuple[str, ...]) -> bool:
    """Case-insensitive substring match of ``text`` on any of ``fields``."""
    needle = text.lower()
    return any(needle in (getattr(item, name, None) or "").lower() for name in fields)


def filtered_page[M: BaseModel](
    candidates: list[M],
    filter: str,
    record: Callable[[M], dict[str, Any]],
    search: str | None,
    search_fields: tuple[str, ...],
    limit: int,
    offset: int,
) -> tuple[list[M], int]:
    """Keep the candidates that match the filter and search, then return one page and the total."""
    matches = parse_filter(filter)
    text = clean_search(search)
    matched = [
        item
        for item in candidates
        if matches(record(item))
        and (text is None or matches_search(item, text, search_fields))
    ]
    return matched[offset : offset + limit], len(matched)
