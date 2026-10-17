from uuid import UUID

from kangaroo.repositories import InvocationRepository
from kangaroo.schemas import Invocation, PaginatedResponse


class InvocationService:
    """Reads the stored runs of saved scripts."""

    def __init__(self, invocations: InvocationRepository) -> None:
        self._invocations = invocations

    def get(self, item_id: UUID) -> Invocation:
        return self._invocations.get_by_id(item_id)

    def list_paginated(
        self, limit: int, offset: int, function_id: UUID | None = None
    ) -> PaginatedResponse[Invocation]:
        return self._invocations.list_paginated(
            limit, offset, None, function_id=function_id
        )
