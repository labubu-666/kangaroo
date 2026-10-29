from uuid import UUID

from fastapi import APIRouter, status

from kangaroo.routes.dependencies import FilterQuery, ListParamsDep, WorkItemServiceDep
from kangaroo.schemas import (
    PaginatedResponse,
    WorkItemBulkDelete,
    WorkItemBulkDeleted,
    WorkItemCreate,
    WorkItemDetail,
    WorkItemReplace,
    WorkItemUpdate,
)

router = APIRouter(prefix="/work-items", tags=["work-items"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=WorkItemDetail)
def create_work_item(
    item: WorkItemCreate,
    service: WorkItemServiceDep,
) -> WorkItemDetail:
    """Create a new work item in the given project, optionally under a parent."""
    return service.create(item)


@router.get("/", response_model=PaginatedResponse[WorkItemDetail])
def list_work_items(
    params: ListParamsDep,
    service: WorkItemServiceDep,
    project_id: UUID | None = None,
    parent_id: UUID | None = None,
    filter: FilterQuery = None,
) -> PaginatedResponse[WorkItemDetail]:
    """List work items with pagination.

    Args:
        limit: The maximum number of items to return (default: 10, max: 100).
        offset: The number of items to skip from the beginning (default: 0).
        project_id: Optional project ID to filter work items by.
        parent_id: Optional parent work item ID to list the children of.
        search: Optional text to match case-insensitively in summary or description.
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
def get_work_item(item_id: UUID, service: WorkItemServiceDep) -> WorkItemDetail:
    """Get a work item by ID."""
    return service.get(item_id)


@router.put("/{item_id}", response_model=WorkItemDetail)
def replace_work_item(
    item_id: UUID,
    replace: WorkItemReplace,
    service: WorkItemServiceDep,
) -> WorkItemDetail:
    """Replace a work item (full update)."""
    return service.replace(item_id, replace)


@router.patch("/{item_id}", response_model=WorkItemDetail)
def update_work_item(
    item_id: UUID,
    update: WorkItemUpdate,
    service: WorkItemServiceDep,
) -> WorkItemDetail:
    """Update a work item (partial update)."""
    return service.update(item_id, update)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_work_item(item_id: UUID, service: WorkItemServiceDep) -> None:
    """Delete a work item and its children."""
    service.delete(item_id)


@router.post(
    "/{item_id}/duplicate",
    status_code=status.HTTP_201_CREATED,
    response_model=WorkItemDetail,
)
def duplicate_work_item(item_id: UUID, service: WorkItemServiceDep) -> WorkItemDetail:
    """Create a copy of a work item. Its children are not copied."""
    return service.duplicate(item_id)


@router.post("/bulk-delete", response_model=WorkItemBulkDeleted)
def bulk_delete_work_items(
    request: WorkItemBulkDelete,
    service: WorkItemServiceDep,
) -> WorkItemBulkDeleted:
    """Delete the given work items, or every item the filter matches.

    Children are deleted with their parent. An invalid filter returns 422.
    """
    return WorkItemBulkDeleted(deleted=service.bulk_delete(request))
