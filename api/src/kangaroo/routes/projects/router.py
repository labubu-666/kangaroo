from uuid import UUID

from fastapi import APIRouter, status

from kangaroo.routes.dependencies import ListParamsDep, ProjectServiceDep
from kangaroo.schemas import (
    PaginatedResponse,
    Project,
    ProjectCreate,
    ProjectCreateRequest,
    ProjectReplace,
    ProjectUpdate,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Project)
def create_project(item: ProjectCreateRequest, service: ProjectServiceDep) -> Project:
    """Create a new project from a template (default "To Do List").

    An unknown template returns 400. The template is only used here: a project
    keeps its statuses and types after it is created.
    """
    return service.create(
        ProjectCreate(name=item.name, description=item.description, labels=item.labels),
        template=item.template,
    )


@router.get("/", response_model=PaginatedResponse[Project])
def list_projects(
    params: ListParamsDep,
    service: ProjectServiceDep,
) -> PaginatedResponse[Project]:
    """List projects with pagination.

    Args:
        limit: The maximum number of items to return (default: 10, max: 100).
        offset: The number of items to skip from the beginning (default: 0).
        search: Optional text to match case-insensitively in name or description.

    Returns:
        A paginated response containing items and metadata.
    """
    return service.list_paginated(params.limit, params.offset, params.search)


@router.get("/{item_id}", response_model=Project)
def get_project(item_id: UUID, service: ProjectServiceDep) -> Project:
    """Get a project by ID."""
    return service.get(item_id)


@router.put("/{item_id}", response_model=Project)
def replace_project(
    item_id: UUID,
    replace: ProjectReplace,
    service: ProjectServiceDep,
) -> Project:
    """Replace a project (full update)."""
    return service.replace(item_id, replace)


@router.patch("/{item_id}", response_model=Project)
def update_project(
    item_id: UUID,
    update: ProjectUpdate,
    service: ProjectServiceDep,
) -> Project:
    """Update a project (partial update)."""
    return service.update(item_id, update)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(item_id: UUID, service: ProjectServiceDep) -> None:
    """Delete a project.

    A project that still has work items or boards cannot be deleted (409).
    """
    service.delete(item_id)
