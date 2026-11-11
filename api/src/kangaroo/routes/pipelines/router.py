from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, status

from kangaroo.routes.auth import require_user
from kangaroo.routes.dependencies import ListParamsDep, PipelineServiceDep
from kangaroo.schemas import (
    PaginatedResponse,
    Pipeline,
    PipelineCreate,
    PipelineReplace,
    PipelineRun,
    PipelineUpdate,
)

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Pipeline)
def create_pipeline(item: PipelineCreate, service: PipelineServiceDep) -> Pipeline:
    """Save a new pipeline: a map from function name to its on_success/on_failure."""
    return service.create(item)


@router.get("/", response_model=PaginatedResponse[Pipeline])
def list_pipelines(
    params: ListParamsDep,
    service: PipelineServiceDep,
) -> PaginatedResponse[Pipeline]:
    """List pipelines with pagination, search and sort."""
    return service.list_paginated(
        params.limit, params.offset, params.search, params.sort
    )


@router.get("/{item_id}", response_model=Pipeline)
def get_pipeline(item_id: UUID, service: PipelineServiceDep) -> Pipeline:
    """Get a pipeline by ID."""
    return service.get(item_id)


@router.put("/{item_id}", response_model=Pipeline)
def replace_pipeline(
    item_id: UUID, replace: PipelineReplace, service: PipelineServiceDep
) -> Pipeline:
    """Replace a pipeline (full update)."""
    return service.replace(item_id, replace)


@router.patch("/{item_id}", response_model=Pipeline)
def update_pipeline(
    item_id: UUID, update: PipelineUpdate, service: PipelineServiceDep
) -> Pipeline:
    """Update a pipeline (partial update)."""
    return service.update(item_id, update)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pipeline(item_id: UUID, service: PipelineServiceDep) -> None:
    """Delete a pipeline."""
    service.delete(item_id)


@router.post("/{item_id}/run", status_code=status.HTTP_202_ACCEPTED)
def run_pipeline(
    item_id: UUID,
    service: PipelineServiceDep,
    user: Annotated[dict[str, Any], Depends(require_user)],
) -> dict[str, UUID]:
    """Queue a run. The worker carries it out; this returns the run's ID at once.

    The run's steps act as the user who started it.
    """
    return {"run_id": service.start_run(item_id, started_by=user)}


@router.get("/{item_id}/runs", response_model=PaginatedResponse[PipelineRun])
def list_pipeline_runs(
    item_id: UUID,
    params: ListParamsDep,
    service: PipelineServiceDep,
) -> PaginatedResponse[PipelineRun]:
    """List a pipeline's runs, newest first, with pagination."""
    return service.list_runs(item_id, params.limit, params.offset)
