from uuid import UUID

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from kangaroo.repositories import (
    FunctionRepository,
    InvocationRepository,
)
from kangaroo.runners import BaseRunner, RunnerUnavailableError
from kangaroo.schemas import (
    Function,
    FunctionCreate,
    FunctionReplace,
    FunctionUpdate,
    Invocation,
    InvocationCreate,
    InvocationUpdate,
    PaginatedResponse,
    RunRequest,
)


class FunctionService:
    """Stores saved scripts and runs them through a runner."""

    def __init__(
        self,
        functions: FunctionRepository,
        engine: Engine,
        runner: BaseRunner,
    ) -> None:
        self._functions = functions
        self._engine = engine
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

    def run(self, item_id: UUID, env: dict[str, str] | None = None) -> Invocation:
        """Run a saved script through the configured runner and store the outcome.

        The invocation is stored as RUNNING before the script starts, so the row exists
        while it runs, and is updated once the script has finished.
        ``env`` is added to the script's environment, for example its API token.

        Each write commits in its own short transaction. The script calls back into
        this API, and a transaction left open here would hold SQLite's write lock
        and make those calls fail with "database is locked".

        Raises:
            RunnerUnavailableError: If the runner cannot be reached. The invocation
                is then stored as ERROR.
        """
        function = self._functions.get_by_id(item_id)
        invocation = self._write(
            lambda invocations: invocations.create(
                InvocationCreate(function_id=function.id, status="RUNNING")
            )
        )
        try:
            result = self._runner.run(RunRequest(code=function.code, env=env or {}))
        except RunnerUnavailableError as exc:
            error = str(exc)
            self._write(
                lambda invocations: invocations.update(
                    invocation.id, InvocationUpdate(status="ERROR", error=error)
                )
            )
            raise
        return self._write(
            lambda invocations: invocations.update(
                invocation.id, InvocationUpdate(**result.model_dump())
            )
        )

    def _write(self, action):
        """Run one repository write in its own transaction and return its result."""
        with Session(self._engine, expire_on_commit=False) as session, session.begin():
            return action(InvocationRepository(session))
