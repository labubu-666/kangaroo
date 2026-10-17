from uuid import UUID

from fastapi import APIRouter, status

from kangaroo.routes.dependencies import BoardServiceDep, FilterQuery, ListParamsDep
from kangaroo.schemas import (
    Board,
    BoardCreate,
    BoardReplace,
    BoardUpdate,
    BoardView,
    PaginatedResponse,
)

router = APIRouter(prefix="/boards", tags=["boards"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Board)
def create_board(item: BoardCreate, service: BoardServiceDep) -> Board:
    """Create a new board. The filter must be valid filter syntax (422 otherwise)."""
    return service.create(item)


@router.get("/", response_model=PaginatedResponse[Board])
def list_boards(
    params: ListParamsDep,
    service: BoardServiceDep,
    project_id: UUID | None = None,
    filter: FilterQuery = None,
) -> PaginatedResponse[Board]:
    """List boards with pagination.

    Args:
        limit: The maximum number of items to return (default: 10, max: 100).
        offset: The number of items to skip from the beginning (default: 0).
        search: Optional text to match case-insensitively in name or description.
        project_id: Optional project ID to list only that project's boards.
        filter: Optional filter in the filter language, e.g.
            ``project.id == '<uuid>'``. Invalid filters return 422.

    Returns:
        A paginated response containing items and metadata.
    """
    return service.list_paginated(
        params.limit,
        params.offset,
        params.search,
        project_id=project_id,
        filter=filter,
    )


@router.get("/{item_id}", response_model=Board)
def get_board(item_id: UUID, service: BoardServiceDep) -> Board:
    """Get a board by ID."""
    return service.get(item_id)


@router.get("/{item_id}/view", response_model=BoardView)
def view_board(item_id: UUID, service: BoardServiceDep) -> BoardView:
    """Get the board's work items that match its filter, grouped by status."""
    return service.view(item_id)


@router.put("/{item_id}", response_model=Board)
def replace_board(
    item_id: UUID,
    replace: BoardReplace,
    service: BoardServiceDep,
) -> Board:
    """Replace a board (full update)."""
    return service.replace(item_id, replace)


@router.patch("/{item_id}", response_model=Board)
def update_board(
    item_id: UUID,
    update: BoardUpdate,
    service: BoardServiceDep,
) -> Board:
    """Update a board (partial update)."""
    return service.update(item_id, update)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_board(item_id: UUID, service: BoardServiceDep) -> None:
    """Delete a board."""
    service.delete(item_id)
