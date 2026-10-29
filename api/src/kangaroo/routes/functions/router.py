from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, status

from kangaroo.routes.auth import create_impersonation_token, require_user
from kangaroo.routes.dependencies import FunctionServiceDep, ListParamsDep
from kangaroo.schemas import (
    Function,
    FunctionCreate,
    FunctionReplace,
    FunctionUpdate,
    Invocation,
    PaginatedResponse,
)
from kangaroo.settings import settings

router = APIRouter(prefix="/functions", tags=["functions"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Function)
def create_function(item: FunctionCreate, service: FunctionServiceDep) -> Function:
    """Save a new function (a Python script)."""
    return service.create(item)


@router.get("/", response_model=PaginatedResponse[Function])
def list_functions(
    params: ListParamsDep,
    service: FunctionServiceDep,
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
def get_function(item_id: UUID, service: FunctionServiceDep) -> Function:
    """Get a function by ID."""
    return service.get(item_id)


@router.put("/{item_id}", response_model=Function)
def replace_function(
    item_id: UUID,
    replace: FunctionReplace,
    service: FunctionServiceDep,
) -> Function:
    """Replace a function (full update)."""
    return service.replace(item_id, replace)


@router.patch("/{item_id}", response_model=Function)
def update_function(
    item_id: UUID,
    update: FunctionUpdate,
    service: FunctionServiceDep,
) -> Function:
    """Update a function (partial update)."""
    return service.update(item_id, update)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_function(item_id: UUID, service: FunctionServiceDep) -> None:
    """Delete a function."""
    service.delete(item_id)


@router.post("/{item_id}/run", response_model=Invocation)
def run_function(
    item_id: UUID,
    service: FunctionServiceDep,
    user: Annotated[dict[str, Any], Depends(require_user)],
) -> Invocation:
    """Run a saved function and store the run as an invocation.

    Returns the stored invocation with its status (SUCCESS or ERROR), logs, result
    and error. The run takes up to 15 seconds. A timeout returns ERROR. If the
    configured runner cannot be reached, the invocation is stored as ERROR and the
    route returns 503.

    The script gets ``KANGAROO_API_URL`` and ``KANGAROO_TOKEN`` in its environment.
    The token impersonates the calling user and expires shortly after the run.
    """
    env = {
        "KANGAROO_API_URL": settings.api_public_url,
        "KANGAROO_TOKEN": create_impersonation_token(user),
    }
    return service.run(item_id, env)
