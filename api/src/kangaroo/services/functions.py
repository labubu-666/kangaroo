from uuid import UUID

from kangaroo.backends import (
    FunctionBackend,
)
from kangaroo.runners import BaseRunner
from kangaroo.schemas import (
    Function,
    FunctionCreate,
    FunctionReplace,
    FunctionUpdate,
    PaginatedResponse,
    RunRequest,
    RunResult,
)


class FunctionService:
    """Stores saved scripts and runs them through a runner."""

    def __init__(self, functions: FunctionBackend, runner: BaseRunner) -> None:
        self._functions = functions
        self._runner = runner

    def create(self, item: FunctionCreate) -> Function:
        return self._functions.create(item)

    def get(self, item_id: UUID) -> Function:
        return self._functions.get_by_id(item_id)

    def list_paginated(
        self, limit: int, offset: int, search: str | None = None
    ) -> PaginatedResponse[Function]:
        return self._functions.list_paginated(limit, offset, search)

    def replace(self, item_id: UUID, replace: FunctionReplace) -> Function:
        return self._functions.replace(item_id, replace)

    def update(self, item_id: UUID, update: FunctionUpdate) -> Function:
        return self._functions.update(item_id, update)

    def delete(self, item_id: UUID) -> None:
        self._functions.delete(item_id)

    def run(self, item_id: UUID) -> RunResult:
        """Run a saved script through the configured runner."""
        function = self._functions.get_by_id(item_id)
        return self._runner.run(RunRequest(code=function.code))
