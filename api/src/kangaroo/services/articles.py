from uuid import UUID

from kangaroo.repositories import ArticleRepository, KnowledgeBaseRepository
from kangaroo.schemas import (
    Article,
    ArticleCreate,
    ArticleDetail,
    ArticleReplace,
    ArticleUpdate,
    PaginatedResponse,
)
from kangaroo.services.helpers import ensure_knowledge_base_exists
from kangaroo.utils import render_markdown


class ArticleService:
    """Stores knowledge base articles and renders their Markdown for display."""

    def __init__(
        self, articles: ArticleRepository, knowledge_bases: KnowledgeBaseRepository
    ) -> None:
        self._articles = articles
        self._knowledge_bases = knowledge_bases

    def create(self, item: ArticleCreate) -> Article:
        ensure_knowledge_base_exists(self._knowledge_bases, item.knowledge_base_id)
        return self._articles.create(item)

    def get(self, item_id: UUID) -> ArticleDetail:
        self._articles.mark_viewed(item_id)
        article = self._articles.get_by_id(item_id)
        return ArticleDetail(**article.model_dump(), html=render_markdown(article.body))

    def list_paginated(
        self,
        limit: int,
        offset: int,
        search: str | None = None,
        sort: str | None = None,
        knowledge_base_id: UUID | None = None,
    ) -> PaginatedResponse[Article]:
        return self._articles.list_paginated(
            limit, offset, search, sort, knowledge_base_id=knowledge_base_id
        )

    def replace(self, item_id: UUID, replace: ArticleReplace) -> Article:
        ensure_knowledge_base_exists(self._knowledge_bases, replace.knowledge_base_id)
        return self._articles.replace(item_id, replace)

    def update(self, item_id: UUID, update: ArticleUpdate) -> Article:
        if update.knowledge_base_id is not None:
            ensure_knowledge_base_exists(
                self._knowledge_bases, update.knowledge_base_id
            )
        return self._articles.update(item_id, update)

    def delete(self, item_id: UUID) -> None:
        self._articles.delete(item_id)
