from uuid import UUID

from fastapi import APIRouter, Depends, status

from kangaroo.routes.dependencies import ListParams, get_function_service, list_params
from kangaroo.schemas import (
    Function,
    FunctionCreate,
    FunctionReplace,
    FunctionUpdate,
    PaginatedResponse,
    RunResult,
)
from kangaroo.services import FunctionService

router = APIRouter(prefix="/functions", tags=["functions"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Function)
def create_function(
    item: FunctionCreate, service: FunctionService = Depends(get_function_service)
) -> Function:
    """Save a new function (a Python script)."""
    return service.create(item)


@router.get("/", response_model=PaginatedResponse[Function])
def list_functions(
    params: ListParams = Depends(list_params),
    service: FunctionService = Depends(get_function_service),
) -> PaginatedResponse[Function]:
    """List functions with pagination.

    Args:
        limit: The maximum number of items to return (default: 10, max: 100).
        offset: The number of items to skip from the beginning (default: 0).
        search: Optional text to match case-insensitively in name or description.

    Returns:
        A paginated response containing items and metadata.
    """
    return service.list_paginated(params.limit, params.offset, params.search)


@router.get("/{item_id}", response_model=Function)
def get_function(
    item_id: UUID, service: FunctionService = Depends(get_function_service)
) -> Function:
    """Get a function by ID."""
    return service.get(item_id)


@router.put("/{item_id}", response_model=Function)
def replace_function(
    item_id: UUID,
    replace: FunctionReplace,
    service: FunctionService = Depends(get_function_service),
) -> Function:
    """Replace a function (full update)."""
    return service.replace(item_id, replace)


@router.patch("/{item_id}", response_model=Function)
def update_function(
    item_id: UUID,
    update: FunctionUpdate,
    service: FunctionService = Depends(get_function_service),
) -> Function:
    """Update a function (partial update)."""
    return service.update(item_id, update)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_function(
    item_id: UUID, service: FunctionService = Depends(get_function_service)
) -> None:
    """Delete a function."""
    service.delete(item_id)


@router.post("/{item_id}/run", response_model=RunResult)
def run_function(
    item_id: UUID, service: FunctionService = Depends(get_function_service)
) -> RunResult:
    """Run a saved function and return its stdout, stderr and exit code.

    The run takes up to 120 seconds. A timeout returns exit code -1. If the
    configured runner cannot be reached, returns 503.
    """
    return service.run(item_id)
