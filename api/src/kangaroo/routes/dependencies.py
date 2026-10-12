from dataclasses import dataclass

from fastapi import Depends, Query

from kangaroo.backends import (
    BoardBackend,
    FunctionBackend,
    ProjectBackend,
    StatusBackend,
    StatusTransitionBackend,
    WorkItemBackend,
    WorkItemTypeBackend,
    create_backends,
)
from kangaroo.runners import create_runner
from kangaroo.services import (
    BoardService,
    FunctionService,
    ProjectService,
    ReportService,
    WorkflowService,
    WorkItemService,
)
from kangaroo.settings import settings

# Module-level singletons, chosen by DATABASE_URL
(
    _work_item_backend,
    _project_backend,
    _board_backend,
    _status_backend,
    _work_item_type_backend,
    _status_transition_backend,
    _function_backend,
) = create_backends(settings.database_url)


@dataclass(frozen=True)
class ListParams:
    """Pagination and search query parameters shared by the list endpoints."""

    limit: int
    offset: int
    search: str | None


def list_params(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: str | None = Query(None, max_length=200),
) -> ListParams:
    return ListParams(limit=limit, offset=offset, search=search)


def get_work_item_backend() -> WorkItemBackend:
    return _work_item_backend


def get_project_backend() -> ProjectBackend:
    return _project_backend


def get_board_backend() -> BoardBackend:
    return _board_backend


def get_status_backend() -> StatusBackend:
    return _status_backend


def get_work_item_type_backend() -> WorkItemTypeBackend:
    return _work_item_type_backend


def get_status_transition_backend() -> StatusTransitionBackend:
    return _status_transition_backend


def get_function_backend() -> FunctionBackend:
    return _function_backend


_function_runner = create_runner(settings.function_runner, settings.nuclio_runner_url)


def get_function_service(
    functions: FunctionBackend = Depends(get_function_backend),
) -> FunctionService:
    return FunctionService(functions, _function_runner)


def get_work_item_service(
    work_items: WorkItemBackend = Depends(get_work_item_backend),
    projects: ProjectBackend = Depends(get_project_backend),
    statuses: StatusBackend = Depends(get_status_backend),
    types: WorkItemTypeBackend = Depends(get_work_item_type_backend),
    transitions: StatusTransitionBackend = Depends(get_status_transition_backend),
) -> WorkItemService:
    return WorkItemService(work_items, projects, statuses, types, transitions)


def get_project_service(
    projects: ProjectBackend = Depends(get_project_backend),
    work_items: WorkItemBackend = Depends(get_work_item_backend),
    boards: BoardBackend = Depends(get_board_backend),
    statuses: StatusBackend = Depends(get_status_backend),
    types: WorkItemTypeBackend = Depends(get_work_item_type_backend),
    transitions: StatusTransitionBackend = Depends(get_status_transition_backend),
) -> ProjectService:
    return ProjectService(projects, work_items, boards, statuses, types, transitions)


def get_workflow_service(
    projects: ProjectBackend = Depends(get_project_backend),
    statuses: StatusBackend = Depends(get_status_backend),
    types: WorkItemTypeBackend = Depends(get_work_item_type_backend),
    transitions: StatusTransitionBackend = Depends(get_status_transition_backend),
    work_items: WorkItemBackend = Depends(get_work_item_backend),
) -> WorkflowService:
    return WorkflowService(projects, statuses, types, transitions, work_items)


def get_board_service(
    boards: BoardBackend = Depends(get_board_backend),
    work_items: WorkItemBackend = Depends(get_work_item_backend),
    projects: ProjectBackend = Depends(get_project_backend),
    statuses: StatusBackend = Depends(get_status_backend),
    types: WorkItemTypeBackend = Depends(get_work_item_type_backend),
) -> BoardService:
    return BoardService(boards, work_items, projects, statuses, types)


def get_report_service(
    work_items: WorkItemBackend = Depends(get_work_item_backend),
    projects: ProjectBackend = Depends(get_project_backend),
    boards: BoardBackend = Depends(get_board_backend),
    statuses: StatusBackend = Depends(get_status_backend),
) -> ReportService:
    return ReportService(work_items, projects, boards, statuses)
