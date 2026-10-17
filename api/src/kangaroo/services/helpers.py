from typing import Any
from uuid import UUID

from kangaroo.errors import (
    InvalidReferenceError,
    NotFoundError,
)
from kangaroo.repositories import (
    ProjectRepository,
    StatusRepository,
    WorkItemTypeRepository,
)
from kangaroo.repositories.repositories import Repository
from kangaroo.schemas import (
    ProjectStatus,
    StatusRef,
    TypeRef,
    WorkItem,
    WorkItemDetail,
    WorkItemType,
)


def _ensure_project_exists(
    projects: ProjectRepository, project_id: UUID | None
) -> None:
    """Raise InvalidReferenceError if the project is null or does not exist."""
    if project_id is None:
        raise InvalidReferenceError("project_id cannot be null")
    try:
        projects.get_by_id(project_id)
    except NotFoundError:
        raise InvalidReferenceError("Project not found") from None


def _project_names(projects: ProjectRepository) -> dict[UUID, str]:
    """Map each project ID to its name."""
    return {project.id: project.name for project in projects.list_all()}


def _filter_record(
    item: WorkItem,
    project_names: dict[UUID, str],
    statuses: dict[UUID, ProjectStatus],
    types: dict[UUID, WorkItemType],
) -> dict[str, Any]:
    """Flatten a work item into the record that filter predicates read."""
    status = statuses.get(item.status_id)
    work_item_type = types.get(item.type_id)
    return {
        "title": item.title,
        "description": item.description,
        "status": status.name if status else None,
        "status_id": str(item.status_id),
        "statusCategory": status.category if status else None,
        "type": work_item_type.name if work_item_type else None,
        "type_id": str(item.type_id),
        "typeLevel": work_item_type.level if work_item_type else None,
        "parent_id": str(item.parent_id) if item.parent_id else None,
        "project.id": str(item.project_id),
        "project.name": project_names.get(item.project_id),
        "labels": item.labels,
        "trashed": "true" if item.trashed else "false",
    }


def _lookups(
    statuses: StatusRepository, types: WorkItemTypeRepository
) -> tuple[dict[UUID, ProjectStatus], dict[UUID, WorkItemType]]:
    """Map every status ID and work item type ID to its row."""
    return (
        {status.id: status for status in statuses.list_all()},
        {work_item_type.id: work_item_type for work_item_type in types.list_all()},
    )


def _detail(
    item: WorkItem,
    statuses: dict[UUID, ProjectStatus],
    types: dict[UUID, WorkItemType],
) -> WorkItemDetail:
    """Add the item's status and type to the stored work item."""
    status = statuses[item.status_id]
    work_item_type = types[item.type_id]
    return WorkItemDetail(
        **item.model_dump(exclude={"rendered_description"}),
        status=StatusRef(id=status.id, name=status.name, category=status.category),
        type=TypeRef(
            id=work_item_type.id, name=work_item_type.name, level=work_item_type.level
        ),
    )


def _next_position(repository: Repository, project_id: UUID) -> int:
    """Place a new item after the last position already used in the project."""
    positions = [item.position for item in repository.list_all(project_id=project_id)]
    return max(positions, default=-1) + 1


def _in_position_order[M: (ProjectStatus, WorkItemType)](items: list[M]) -> list[M]:
    """Sort by position. Items that share a position keep their creation order."""
    return sorted(items, key=lambda item: item.position)
