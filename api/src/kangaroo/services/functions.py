from uuid import UUID

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from kangaroo.errors import ConflictError
from kangaroo.repositories import (
    FunctionRepository,
    InvocationRepository,
)
from kangaroo.runners import BaseRunner
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
        self._check_name_free(item.name)
        return self._functions.create(item)

    def _check_name_free(self, name: str, except_id: UUID | None = None) -> None:
        """Function names are unique, because pipelines refer to functions by name."""
        for existing in self._functions.list_all(name=name):
            if existing.id != except_id:
                raise ConflictError(f"A function named {name!r} already exists")

    def get(self, item_id: UUID) -> Function:
        return self._functions.get_by_id(item_id)

    def list_paginated(
        self,
        limit: int,
        offset: int,
        search: str | None = None,
        sort: str | None = None,
    ) -> PaginatedResponse[Function]:
        return self._functions.list_paginated(limit, offset, search, sort)

    def replace(self, item_id: UUID, replace: FunctionReplace) -> Function:
        self._check_name_free(replace.name, except_id=item_id)
        return self._functions.replace(item_id, replace)

    def update(self, item_id: UUID, update: FunctionUpdate) -> Function:
        if update.name is not None:
            self._check_name_free(update.name, except_id=item_id)
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
                is then stored as ERROR, as it is for any other runner failure.
        """
        function = self._functions.get_by_id(item_id)
        invocation = self._write(
            lambda invocations: invocations.create(
                InvocationCreate(function_id=function.id, status="RUNNING")
            )
        )
        try:
            result = self._runner.run(RunRequest(code=function.code, env=env or {}))
        except Exception as exc:
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
