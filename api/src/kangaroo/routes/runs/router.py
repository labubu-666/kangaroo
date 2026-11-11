from uuid import UUID

from fastapi import APIRouter

from kangaroo.routes.dependencies import ListParamsDep, PipelineServiceDep
from kangaroo.schemas import PaginatedResponse, PipelineRun

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("/", response_model=PaginatedResponse[PipelineRun])
def list_runs(
    params: ListParamsDep,
    service: PipelineServiceDep,
    pipeline_id: UUID | None = None,
) -> PaginatedResponse[PipelineRun]:
    """List runs of all pipelines, newest first, optionally for one pipeline."""
    return service.list_all_runs(params.limit, params.offset, pipeline_id)


@router.get("/{run_id}", response_model=PipelineRun)
def get_run(run_id: UUID, service: PipelineServiceDep) -> PipelineRun:
    """Get a pipeline run with the status of each of its steps."""
    return service.get_run(run_id)
