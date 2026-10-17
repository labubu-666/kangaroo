from collections.abc import Iterator
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy.orm import Session

from kangaroo.backends import Backends, create_backends
from kangaroo.runners import BaseRunner, create_runner
from kangaroo.services import (
    BoardService,
    FunctionService,
    ProjectService,
    ReportService,
    WorkflowService,
    WorkItemService,
)
from kangaroo.settings import settings


@lru_cache
def get_function_runner() -> BaseRunner:
    """Build the function runner from settings on first use, then reuse it."""
    return create_runner(settings.function_runner, settings.nuclio_runner_url)


@dataclass(frozen=True)
class ListParams:
    """Pagination and search query parameters shared by the list endpoints."""

    limit: int
    offset: int
    search: str | None


def list_params(
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
    search: Annotated[str | None, Query(max_length=200)] = None,
) -> ListParams:
    return ListParams(limit=limit, offset=offset, search=search)


@lru_cache
def get_backends() -> Backends:
    """Build the backends from DATABASE_URL on first use, then reuse them."""
    return create_backends(settings.database_url)


def get_request_backends(
    backends: Annotated[Backends, Depends(get_backends)],
) -> Iterator[Backends]:
    """One transaction per request: every backend call the request makes shares it.

    The changes are committed when the route returns normally, and rolled back
    if it raises, so a failed request saves nothing.
    """
    with Session(backends.engine, expire_on_commit=False) as session, session.begin():
        yield backends.bound(session)


def get_function_service(
    backends: Annotated[Backends, Depends(get_request_backends)],
) -> FunctionService:
    return FunctionService(backends.functions, get_function_runner())


def get_work_item_service(
    backends: Annotated[Backends, Depends(get_request_backends)],
) -> WorkItemService:
    return WorkItemService(
        work_items=backends.work_items,
        projects=backends.projects,
        statuses=backends.statuses,
        types=backends.types,
        transitions=backends.transitions,
    )


def get_project_service(
    backends: Annotated[Backends, Depends(get_request_backends)],
) -> ProjectService:
    return ProjectService(
        projects=backends.projects,
        work_items=backends.work_items,
        boards=backends.boards,
        statuses=backends.statuses,
        types=backends.types,
        transitions=backends.transitions,
    )


def get_workflow_service(
    backends: Annotated[Backends, Depends(get_request_backends)],
) -> WorkflowService:
    return WorkflowService(
        projects=backends.projects,
        statuses=backends.statuses,
        types=backends.types,
        transitions=backends.transitions,
        work_items=backends.work_items,
    )


def get_board_service(
    backends: Annotated[Backends, Depends(get_request_backends)],
) -> BoardService:
    return BoardService(
        boards=backends.boards,
        work_items=backends.work_items,
        projects=backends.projects,
        statuses=backends.statuses,
        types=backends.types,
    )


def get_report_service(
    backends: Annotated[Backends, Depends(get_request_backends)],
) -> ReportService:
    return ReportService(
        work_items=backends.work_items,
        projects=backends.projects,
        boards=backends.boards,
        statuses=backends.statuses,
    )


ListParamsDep = Annotated[ListParams, Depends(list_params)]
FilterQuery = Annotated[str | None, Query(max_length=1000)]
FunctionServiceDep = Annotated[FunctionService, Depends(get_function_service)]
WorkItemServiceDep = Annotated[WorkItemService, Depends(get_work_item_service)]
ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]
WorkflowServiceDep = Annotated[WorkflowService, Depends(get_workflow_service)]
BoardServiceDep = Annotated[BoardService, Depends(get_board_service)]
ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]
