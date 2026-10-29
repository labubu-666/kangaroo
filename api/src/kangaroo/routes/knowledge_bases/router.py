from uuid import UUID

from fastapi import APIRouter, status

from kangaroo.routes.dependencies import KnowledgeBaseServiceDep, ListParamsDep
from kangaroo.schemas import (
    KnowledgeBase,
    KnowledgeBaseCreate,
    KnowledgeBaseReplace,
    KnowledgeBaseUpdate,
    PaginatedResponse,
)

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=KnowledgeBase)
def create_knowledge_base(
    item: KnowledgeBaseCreate, service: KnowledgeBaseServiceDep
) -> KnowledgeBase:
    """Create a knowledge base."""
    return service.create(item)


@router.get("/", response_model=PaginatedResponse[KnowledgeBase])
def list_knowledge_bases(
    params: ListParamsDep,
    service: KnowledgeBaseServiceDep,
) -> PaginatedResponse[KnowledgeBase]:
    """List knowledge bases with pagination.

    Args:
        limit: The maximum number of items to return (default: 10, max: 100).
        offset: The number of items to skip from the beginning (default: 0).
        search: Optional text to match case-insensitively in name or description.

    Returns:
        A paginated response containing items and metadata.
    """
    return service.list_paginated(params.limit, params.offset, params.search)


@router.get("/{item_id}", response_model=KnowledgeBase)
def get_knowledge_base(
    item_id: UUID, service: KnowledgeBaseServiceDep
) -> KnowledgeBase:
    """Get a knowledge base by ID."""
    return service.get(item_id)


@router.put("/{item_id}", response_model=KnowledgeBase)
def replace_knowledge_base(
    item_id: UUID,
    replace: KnowledgeBaseReplace,
    service: KnowledgeBaseServiceDep,
) -> KnowledgeBase:
    """Replace a knowledge base (full update)."""
    return service.replace(item_id, replace)


@router.patch("/{item_id}", response_model=KnowledgeBase)
def update_knowledge_base(
    item_id: UUID,
    update: KnowledgeBaseUpdate,
    service: KnowledgeBaseServiceDep,
) -> KnowledgeBase:
    """Update a knowledge base (partial update)."""
    return service.update(item_id, update)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_base(item_id: UUID, service: KnowledgeBaseServiceDep) -> None:
    """Delete a knowledge base.

    A knowledge base that still has articles cannot be deleted (409).
    """
    service.delete(item_id)
