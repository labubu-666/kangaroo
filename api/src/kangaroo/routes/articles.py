from uuid import UUID

from fastapi import APIRouter, status

from kangaroo.routes.dependencies import ArticleServiceDep, ListParamsDep
from kangaroo.schemas import (
    Article,
    ArticleCreate,
    ArticleDetail,
    ArticleReplace,
    ArticleUpdate,
    PaginatedResponse,
)

router = APIRouter(prefix="/articles", tags=["articles"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Article)
def create_article(item: ArticleCreate, service: ArticleServiceDep) -> Article:
    """Create a knowledge base article."""
    return service.create(item)


@router.get("/", response_model=PaginatedResponse[Article])
def list_articles(
    params: ListParamsDep,
    service: ArticleServiceDep,
) -> PaginatedResponse[Article]:
    """List articles with pagination.

    Args:
        limit: The maximum number of items to return (default: 10, max: 100).
        offset: The number of items to skip from the beginning (default: 0).
        search: Optional text to match case-insensitively in title or body.

    Returns:
        A paginated response containing items and metadata.
    """
    return service.list_paginated(params.limit, params.offset, params.search)


@router.get("/{item_id}", response_model=ArticleDetail)
def get_article(item_id: UUID, service: ArticleServiceDep) -> ArticleDetail:
    """Get an article by ID, with its body rendered to HTML."""
    return service.get(item_id)


@router.put("/{item_id}", response_model=Article)
def replace_article(
    item_id: UUID,
    replace: ArticleReplace,
    service: ArticleServiceDep,
) -> Article:
    """Replace an article (full update)."""
    return service.replace(item_id, replace)


@router.patch("/{item_id}", response_model=Article)
def update_article(
    item_id: UUID,
    update: ArticleUpdate,
    service: ArticleServiceDep,
) -> Article:
    """Update an article (partial update)."""
    return service.update(item_id, update)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(item_id: UUID, service: ArticleServiceDep) -> None:
    """Delete an article."""
    service.delete(item_id)
