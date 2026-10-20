from uuid import UUID

from kangaroo.repositories import ArticleRepository
from kangaroo.schemas import (
    Article,
    ArticleCreate,
    ArticleDetail,
    ArticleReplace,
    ArticleUpdate,
    PaginatedResponse,
)
from kangaroo.utils import render_markdown


class ArticleService:
    """Stores knowledge base articles and renders their Markdown for display."""

    def __init__(self, articles: ArticleRepository) -> None:
        self._articles = articles

    def create(self, item: ArticleCreate) -> Article:
        return self._articles.create(item)

    def get(self, item_id: UUID) -> ArticleDetail:
        article = self._articles.get_by_id(item_id)
        return ArticleDetail(**article.model_dump(), html=render_markdown(article.body))

    def list_paginated(
        self, limit: int, offset: int, search: str | None = None
    ) -> PaginatedResponse[Article]:
        return self._articles.list_paginated(limit, offset, search)

    def replace(self, item_id: UUID, replace: ArticleReplace) -> Article:
        return self._articles.replace(item_id, replace)

    def update(self, item_id: UUID, update: ArticleUpdate) -> Article:
        return self._articles.update(item_id, update)

    def delete(self, item_id: UUID) -> None:
        self._articles.delete(item_id)
