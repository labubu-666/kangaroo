from uuid import UUID

from kangaroo.errors import ConflictError
from kangaroo.repositories import ArticleRepository, KnowledgeBaseRepository
from kangaroo.schemas import (
    KnowledgeBase,
    KnowledgeBaseCreate,
    KnowledgeBaseReplace,
    KnowledgeBaseUpdate,
    PaginatedResponse,
)


class KnowledgeBaseService:
    """Business rules for knowledge bases."""

    def __init__(
        self,
        knowledge_bases: KnowledgeBaseRepository,
        articles: ArticleRepository,
    ) -> None:
        self._knowledge_bases = knowledge_bases
        self._articles = articles

    def create(self, item: KnowledgeBaseCreate) -> KnowledgeBase:
        return self._knowledge_bases.create(item)

    def get(self, item_id: UUID) -> KnowledgeBase:
        return self._knowledge_bases.get_by_id(item_id)

    def list_paginated(
        self, limit: int, offset: int, search: str | None = None
    ) -> PaginatedResponse[KnowledgeBase]:
        return self._knowledge_bases.list_paginated(limit, offset, search)

    def replace(self, item_id: UUID, replace: KnowledgeBaseReplace) -> KnowledgeBase:
        return self._knowledge_bases.replace(item_id, replace)

    def update(self, item_id: UUID, update: KnowledgeBaseUpdate) -> KnowledgeBase:
        return self._knowledge_bases.update(item_id, update)

    def delete(self, item_id: UUID) -> None:
        """Delete a knowledge base. One that still has articles is protected."""
        if self._articles.count(knowledge_base_id=item_id) > 0:
            raise ConflictError("Knowledge base still has articles")
        self._knowledge_bases.delete(item_id)
