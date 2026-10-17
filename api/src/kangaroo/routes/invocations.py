from uuid import UUID

from fastapi import APIRouter

from kangaroo.routes.dependencies import InvocationServiceDep, ListParamsDep
from kangaroo.schemas import Invocation, PaginatedResponse

router = APIRouter(prefix="/invocations", tags=["invocations"])


@router.get("/", response_model=PaginatedResponse[Invocation])
def list_invocations(
    params: ListParamsDep,
    service: InvocationServiceDep,
    function_id: UUID | None = None,
) -> PaginatedResponse[Invocation]:
    """List invocations, oldest first, with pagination.

    Args:
        limit: The maximum number of items to return (default: 10, max: 100).
        offset: The number of items to skip from the beginning (default: 0).
        function_id: Optional function ID; only its invocations are listed.

    Returns:
        A paginated response containing items and metadata.
    """
    return service.list_paginated(params.limit, params.offset, function_id)


@router.get("/{item_id}", response_model=Invocation)
def get_invocation(item_id: UUID, service: InvocationServiceDep) -> Invocation:
    """Get an invocation by ID."""
    return service.get(item_id)
