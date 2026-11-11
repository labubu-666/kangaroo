"""Carries out queued pipeline runs, one step at a time.

The API only queues a run by writing pipeline_steps rows. ``tick`` runs in the
worker on a schedule: it claims one ready step per run, runs its function, and
records the outcome. A step is claimed with a conditional update, so it can never
run twice.
"""

import logging
from datetime import timedelta
from typing import Any, Protocol, cast
from uuid import UUID

from sqlalchemy import Engine, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from kangaroo.pipeline_graph import (
    FAILURE,
    PENDING,
    RUNNING,
    SKIPPED,
    SUCCESS,
    build_graph,
    plan_next,
)
from kangaroo.repositories import (
    FunctionRepository,
    PipelineRepository,
    PipelineStepRepository,
)
from kangaroo.repositories.repositories import utc_now
from kangaroo.repositories.tables import PipelineRunRow, PipelineStepRow
from kangaroo.routes.auth import create_impersonation_token
from kangaroo.runners import BaseRunner
from kangaroo.schemas import MAX_RUN_TIMEOUT_SECONDS
from kangaroo.services import FunctionService
from kangaroo.settings import settings

logger = logging.getLogger(__name__)

# A step stuck in RUNNING for longer than a run can take has lost its worker.
STUCK_AFTER = timedelta(seconds=MAX_RUN_TIMEOUT_SECONDS * 2)


class StepRunner(Protocol):
    """Runs the saved function a step refers to; returns its invocation ID and outcome."""

    def run(
        self, function_id: UUID, started_by: dict[str, Any] | None
    ) -> tuple[UUID, str]: ...


class FunctionStepRunner:
    """Runs a step by running the saved function it refers to by ID.

    The script gets the same environment as a direct run: the API URL, and a token
    for the user who started the pipeline run. A run with no recorded user gets only
    the URL, because there is no one to impersonate.
    """

    def __init__(self, engine: Engine, runner: BaseRunner) -> None:
        self._engine = engine
        self._runner = runner

    def run(
        self, function_id: UUID, started_by: dict[str, Any] | None
    ) -> tuple[UUID, str]:
        env = {"KANGAROO_API_URL": settings.api_public_url}
        if started_by is not None:
            env["KANGAROO_TOKEN"] = create_impersonation_token(started_by)
        with Session(self._engine) as session, session.begin():
            service = FunctionService(
                FunctionRepository(session), self._engine, self._runner
            )
            invocation = service.run(function_id, env)
        # An invocation ends as SUCCESS or ERROR; a step ends as SUCCESS or FAILURE.
        outcome = SUCCESS if invocation.status == "SUCCESS" else FAILURE
        return invocation.id, outcome


def tick(engine: Engine, runner: StepRunner) -> None:
    """Advance every running pipeline run by at most one step."""
    _recover_stuck_steps(engine)
    with Session(engine) as session, session.begin():
        run_ids = PipelineStepRepository(session).running_run_ids()
    for run_id in run_ids:
        _advance(engine, run_id, runner)


def _recover_stuck_steps(engine: Engine) -> None:
    cutoff = utc_now() - STUCK_AFTER
    with Session(engine) as session, session.begin():
        session.execute(
            update(PipelineStepRow)
            .where(PipelineStepRow.status == RUNNING)
            .where(PipelineStepRow.started_at < cutoff)
            .values(status=FAILURE, modified_at=utc_now())
        )


def _advance(engine: Engine, run_id: UUID, runner: StepRunner) -> None:
    """Skip dead steps, claim one ready step and run it, then finish the run if done."""
    with Session(engine) as session, session.begin():
        rows = PipelineStepRepository(session).steps_for(run_id)
        run = session.get(PipelineRunRow, run_id)
        if run is None:
            return
        steps = PipelineRepository(session).get_by_id(run.pipeline_id).steps
        ready, skipped = plan_next(
            build_graph(steps), {name: row.status for name, row in rows.items()}
        )
        for name in skipped:
            rows[name].status = SKIPPED
            rows[name].modified_at = utc_now()
        claimed = _claim(session, rows, ready)
        if claimed is None:
            _finish_if_done(session, run, rows)
            return
        claimed_id = rows[claimed].id
        function_id = steps[claimed].function_id
        started_by = run.started_by
    _execute(engine, run_id, claimed, claimed_id, function_id, started_by, runner)


def _claim(session: Session, rows, ready: list[str]) -> str | None:
    """Mark the first ready step RUNNING, unless another consumer already did."""
    for name in ready:
        result = cast(
            CursorResult,
            session.execute(
                update(PipelineStepRow)
                .where(PipelineStepRow.id == rows[name].id)
                .where(PipelineStepRow.status == PENDING)
                .values(status=RUNNING, started_at=utc_now(), modified_at=utc_now())
            ),
        )
        if result.rowcount == 1:
            return name
    return None


def _execute(
    engine: Engine,
    run_id: UUID,
    name: str,
    row_id: UUID,
    function_id: UUID,
    started_by: dict[str, Any] | None,
    runner: StepRunner,
) -> None:
    """Run the step, store its outcome, and finish the run if nothing is left."""
    try:
        invocation_id, outcome = runner.run(function_id, started_by)
    except Exception:
        logger.exception("Pipeline step %s raised", name)
        invocation_id, outcome = None, FAILURE
    with Session(engine) as session, session.begin():
        session.execute(
            update(PipelineStepRow)
            .where(PipelineStepRow.id == row_id)
            .values(status=outcome, invocation_id=invocation_id, modified_at=utc_now())
        )
        rows = PipelineStepRepository(session).steps_for(run_id)
        run = session.get(PipelineRunRow, run_id)
        if run is None:
            return
        _finish_if_done(session, run, rows)


def _finish_if_done(session: Session, run: PipelineRunRow, rows) -> None:
    """Mark the run SUCCESS or FAILURE once no step is PENDING or RUNNING."""
    if any(row.status in (PENDING, RUNNING) for row in rows.values()):
        return
    failed = any(row.status == FAILURE for row in rows.values())
    run.status = FAILURE if failed else SUCCESS
    run.modified_at = utc_now()
