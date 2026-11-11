from collections.abc import Mapping
from typing import Any, cast
from uuid import UUID

from kangaroo.errors import NotFoundError
from kangaroo.pipeline_graph import InvalidPipelineError, build_graph
from kangaroo.repositories import (
    FunctionRepository,
    PipelineRepository,
    PipelineStepRepository,
)
from kangaroo.schemas import (
    PaginatedResponse,
    Pipeline,
    PipelineCreate,
    PipelineReplace,
    PipelineRun,
    PipelineStep,
    PipelineStepRun,
    PipelineStepStatus,
    PipelineUpdate,
)


class PipelineService:
    """Stores pipelines and queues their runs for the orchestrator to carry out."""

    def __init__(
        self,
        pipelines: PipelineRepository,
        steps: PipelineStepRepository,
        functions: FunctionRepository,
    ) -> None:
        self._pipelines = pipelines
        self._steps = steps
        self._functions = functions

    def _validate(self, steps: Mapping[str, PipelineStep]) -> None:
        """Check the graph, then check every step refers to a saved function."""
        build_graph(steps)
        for name, step in steps.items():
            try:
                self._functions.get_by_id(step.function_id)
            except NotFoundError:
                raise InvalidPipelineError(
                    f"Step {name!r} refers to a function that does not exist"
                ) from None

    def create(self, item: PipelineCreate) -> Pipeline:
        self._validate(item.steps)
        return self._pipelines.create(item)

    def get(self, item_id: UUID) -> Pipeline:
        return self._pipelines.get_by_id(item_id)

    def list_paginated(
        self,
        limit: int,
        offset: int,
        search: str | None = None,
        sort: str | None = None,
    ) -> PaginatedResponse[Pipeline]:
        return self._pipelines.list_paginated(limit, offset, search, sort)

    def replace(self, item_id: UUID, replace: PipelineReplace) -> Pipeline:
        self._validate(replace.steps)
        return self._pipelines.replace(item_id, replace)

    def update(self, item_id: UUID, update: PipelineUpdate) -> Pipeline:
        if update.steps is not None:
            self._validate(update.steps)
        return self._pipelines.update(item_id, update)

    def delete(self, item_id: UUID) -> None:
        self._pipelines.delete(item_id)

    def start_run(
        self, item_id: UUID, started_by: dict[str, Any] | None = None
    ) -> UUID:
        """Queue a run of a saved pipeline. The orchestrator carries it out.

        ``started_by`` is the user whose token the run's steps will carry.
        """
        pipeline = self._pipelines.get_by_id(item_id)
        return self._steps.create_run(
            pipeline.id, list(pipeline.steps), started_by=started_by
        )

    def get_run(self, run_id: UUID) -> PipelineRun:
        """Return a run with the status of each of its steps.

        Raises:
            NotFoundError: If the run does not exist.
        """
        row = self._steps.get_run(run_id)
        if row is None:
            raise NotFoundError(f"Pipeline run {run_id} not found")
        return self._run_model(row)

    def list_runs(
        self, item_id: UUID, limit: int, offset: int
    ) -> PaginatedResponse[PipelineRun]:
        self._pipelines.get_by_id(item_id)
        rows, total = self._steps.list_runs(limit, offset, pipeline_id=item_id)
        return PaginatedResponse[PipelineRun](
            results=[self._run_model(row) for row in rows],
            limit=limit,
            offset=offset,
            total=total,
        )

    def list_all_runs(
        self, limit: int, offset: int, pipeline_id: UUID | None = None
    ) -> PaginatedResponse[PipelineRun]:
        rows, total = self._steps.list_runs(limit, offset, pipeline_id=pipeline_id)
        return PaginatedResponse[PipelineRun](
            results=[self._run_model(row) for row in rows],
            limit=limit,
            offset=offset,
            total=total,
        )

    def _run_model(self, row) -> PipelineRun:
        steps = self._steps.steps_for(row.id)
        return PipelineRun(
            id=row.id,
            pipeline_id=row.pipeline_id,
            status=row.status,
            created_at=row.created_at,
            modified_at=row.modified_at,
            steps=[
                PipelineStepRun(
                    step=name,
                    status=cast(PipelineStepStatus, step.status),
                    invocation_id=step.invocation_id,
                )
                for name, step in sorted(steps.items())
            ],
        )
