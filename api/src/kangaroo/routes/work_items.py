from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from kangaroo.routes.dependencies import (
    ListParams,
    get_work_item_service,
    list_params,
)
from kangaroo.schemas import (
    PaginatedResponse,
    WorkItemCreate,
    WorkItemDetail,
    WorkItemReplace,
    WorkItemUpdate,
)
from kangaroo.services import WorkItemService

router = APIRouter(prefix="/work-items", tags=["work-items"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=WorkItemDetail)
def create_work_item(
    item: WorkItemCreate,
    service: WorkItemService = Depends(get_work_item_service),
) -> WorkItemDetail:
    """Create a new work item in the given project.

    A subtask must reference a task in the same project via parent_id.
    """
    return service.create(item)


@router.get("/", response_model=PaginatedResponse[WorkItemDetail])
def list_work_items(
    params: ListParams = Depends(list_params),
    project_id: UUID | None = None,
    parent_id: UUID | None = None,
    filter: str | None = Query(None, max_length=1000),
    service: WorkItemService = Depends(get_work_item_service),
) -> PaginatedResponse[WorkItemDetail]:
    """List work items with pagination.

    Args:
        limit: The maximum number of items to return (default: 10, max: 100).
        offset: The number of items to skip from the beginning (default: 0).
        project_id: Optional project ID to filter work items by.
        parent_id: Optional parent work item ID to list the subtasks of.
        search: Optional text to match case-insensitively in title or description.
        filter: Optional filter in the board filter language, e.g.
            ``status == 'in_progress'`` or ``trashed == false``. Invalid filters
            return 422. Trashed items are included unless the filter excludes them.

    Returns:
        A paginated response containing items and metadata.
    """
    return service.list_paginated(
        params.limit,
        params.offset,
        project_id=project_id,
        parent_id=parent_id,
        search=params.search,
        filter=filter,
    )


@router.get("/{item_id}", response_model=WorkItemDetail)
def get_work_item(
    item_id: UUID, service: WorkItemService = Depends(get_work_item_service)
) -> WorkItemDetail:
    """Get a work item by ID."""
    return service.get(item_id)


@router.put("/{item_id}", response_model=WorkItemDetail)
def replace_work_item(
    item_id: UUID,
    replace: WorkItemReplace,
    service: WorkItemService = Depends(get_work_item_service),
) -> WorkItemDetail:
    """Replace a work item (full update)."""
    return service.replace(item_id, replace)


@router.patch("/{item_id}", response_model=WorkItemDetail)
def update_work_item(
    item_id: UUID,
    update: WorkItemUpdate,
    service: WorkItemService = Depends(get_work_item_service),
) -> WorkItemDetail:
    """Update a work item (partial update)."""
    return service.update(item_id, update)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_work_item(
    item_id: UUID, service: WorkItemService = Depends(get_work_item_service)
) -> None:
    """Delete a work item.

    A task that still has subtasks cannot be deleted (409).
    """
    service.delete(item_id)
