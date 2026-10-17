from collections.abc import Iterator
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from kangaroo.repositories import (
    BoardRepository,
    FunctionRepository,
    ProjectRepository,
    StatusRepository,
    StatusTransitionRepository,
    WorkItemRepository,
    WorkItemTypeRepository,
    create_engine_for,
)
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
def get_engine() -> Engine:
    """Create the database engine from DATABASE_URL on first use, then reuse it."""
    return create_engine_for(settings.database_url)


def get_session(engine: Annotated[Engine, Depends(get_engine)]) -> Iterator[Session]:
    """One transaction per request: every repository call the request makes shares it.

    The changes are committed when the route returns normally, and rolled back
    if it raises, so a failed request saves nothing.
    """
    with Session(engine, expire_on_commit=False) as session, session.begin():
        yield session


def get_function_service(
    session: Annotated[Session, Depends(get_session)],
) -> FunctionService:
    return FunctionService(FunctionRepository(session), get_function_runner())


def get_work_item_service(
    session: Annotated[Session, Depends(get_session)],
) -> WorkItemService:
    return WorkItemService(
        work_items=WorkItemRepository(session),
        projects=ProjectRepository(session),
        statuses=StatusRepository(session),
        types=WorkItemTypeRepository(session),
        transitions=StatusTransitionRepository(session),
    )


def get_project_service(
    session: Annotated[Session, Depends(get_session)],
) -> ProjectService:
    return ProjectService(
        projects=ProjectRepository(session),
        work_items=WorkItemRepository(session),
        boards=BoardRepository(session),
        statuses=StatusRepository(session),
        types=WorkItemTypeRepository(session),
        transitions=StatusTransitionRepository(session),
    )


def get_workflow_service(
    session: Annotated[Session, Depends(get_session)],
) -> WorkflowService:
    return WorkflowService(
        projects=ProjectRepository(session),
        statuses=StatusRepository(session),
        types=WorkItemTypeRepository(session),
        transitions=StatusTransitionRepository(session),
        work_items=WorkItemRepository(session),
    )


def get_board_service(
    session: Annotated[Session, Depends(get_session)],
) -> BoardService:
    return BoardService(
        boards=BoardRepository(session),
        work_items=WorkItemRepository(session),
        projects=ProjectRepository(session),
        statuses=StatusRepository(session),
        types=WorkItemTypeRepository(session),
    )


def get_report_service(
    session: Annotated[Session, Depends(get_session)],
) -> ReportService:
    return ReportService(
        work_items=WorkItemRepository(session),
        projects=ProjectRepository(session),
        boards=BoardRepository(session),
        statuses=StatusRepository(session),
    )


ListParamsDep = Annotated[ListParams, Depends(list_params)]
FilterQuery = Annotated[str | None, Query(max_length=1000)]
FunctionServiceDep = Annotated[FunctionService, Depends(get_function_service)]
WorkItemServiceDep = Annotated[WorkItemService, Depends(get_work_item_service)]
ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]
WorkflowServiceDep = Annotated[WorkflowService, Depends(get_workflow_service)]
BoardServiceDep = Annotated[BoardService, Depends(get_board_service)]
ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]
