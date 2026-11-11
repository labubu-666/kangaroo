from datetime import timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from kangaroo.orchestrator import STUCK_AFTER, FunctionStepRunner, tick
from kangaroo.pipeline_graph import FAILURE, RUNNING, SKIPPED, SUCCESS
from kangaroo.repositories import PipelineRepository, PipelineStepRepository
from kangaroo.repositories.repositories import utc_now
from kangaroo.repositories.tables import (
    FunctionRow,
    InvocationRow,
    PipelineRunRow,
    PipelineStepRow,
)
from kangaroo.routes.auth.router import _impersonation_serializer
from kangaroo.runners.base import BaseRunner
from kangaroo.schemas import PipelineCreate, PipelineStep, RunResult


def verify_impersonation_token(token):
    return _impersonation_serializer.loads(token)


class FakeRunner:
    """Records the functions it ran and gives each one a preset outcome.

    Each run stores a real invocation, as FunctionService does, because a step
    refers to its invocation by foreign key.
    """

    def __init__(self, engine, outcomes=None):
        self.engine = engine
        self.outcomes = outcomes or {}
        self.ran = []

    def run(self, function_id, started_by=None):
        with Session(self.engine) as session, session.begin():
            function = session.get(FunctionRow, function_id)
            assert function is not None
            name = function.name
        self.ran.append(name)
        outcome = self.outcomes.get(name, SUCCESS)
        invocation_id = uuid4()
        with Session(self.engine) as session, session.begin():
            session.add(
                InvocationRow(
                    id=invocation_id,
                    function_id=function_id,
                    status=outcome,
                    logs="",
                    created_at=utc_now(),
                    modified_at=utc_now(),
                )
            )
        return invocation_id, outcome


def queue(engine, steps, started_by=None):
    """Save a pipeline from {name: (on_success, on_failure)} and queue one run.

    Each step gets its own saved function, named after the step.
    """
    function_ids = {}
    with Session(engine, expire_on_commit=False) as session, session.begin():
        for name in steps:
            function_ids[name] = uuid4()
            session.add(
                FunctionRow(
                    id=function_ids[name],
                    name=name,
                    code="",
                    created_at=utc_now(),
                    modified_at=utc_now(),
                )
            )
    with Session(engine, expire_on_commit=False) as session, session.begin():
        pipeline = PipelineRepository(session).create(
            PipelineCreate(
                name="p",
                steps={
                    name: PipelineStep(
                        function_id=function_ids[name], on_success=ok, on_failure=fail
                    )
                    for name, (ok, fail) in steps.items()
                },
            )
        )
        return PipelineStepRepository(session).create_run(
            pipeline.id, list(steps), started_by=started_by
        )


def run_status(engine, run_id):
    with Session(engine) as session:
        run = session.get(PipelineRunRow, run_id)
        assert run is not None
        return run.status


def step_states(engine, run_id):
    with Session(engine) as session:
        rows = session.scalars(
            select(PipelineStepRow).where(PipelineStepRow.pipeline_run_id == run_id)
        )
        return {row.step: row.status for row in rows}


def drain(engine, runner, ticks=20):
    for _ in range(ticks):
        tick(engine, runner)


def test_tick_runs_a_pipeline_to_the_end(engine):
    run_id = queue(engine, {"a": (["b"], ["c"]), "b": ([], []), "c": ([], [])})
    runner = FakeRunner(engine)
    drain(engine, runner)
    assert runner.ran == ["a", "b"]
    assert step_states(engine, run_id) == {"a": SUCCESS, "b": SUCCESS, "c": SKIPPED}
    assert run_status(engine, run_id) == SUCCESS


def test_failure_branch_runs_and_run_ends_as_failure(engine):
    run_id = queue(engine, {"a": (["b"], ["c"]), "b": ([], []), "c": ([], [])})
    runner = FakeRunner(engine, {"a": FAILURE})
    drain(engine, runner)
    assert runner.ran == ["a", "c"]
    assert step_states(engine, run_id) == {"a": FAILURE, "b": SKIPPED, "c": SUCCESS}
    assert run_status(engine, run_id) == FAILURE


def test_each_step_runs_at_most_once(engine):
    run_id = queue(engine, {"a": ([], [])})
    runner = FakeRunner(engine)
    drain(engine, runner)
    assert runner.ran == ["a"]
    assert step_states(engine, run_id) == {"a": SUCCESS}


def test_stuck_running_step_is_failed_and_run_finishes(engine):
    run_id = queue(engine, {"a": ([], [])})
    with Session(engine) as session, session.begin():
        row = session.scalars(
            select(PipelineStepRow).where(PipelineStepRow.pipeline_run_id == run_id)
        ).one()
        row.status = RUNNING
        row.started_at = utc_now() - STUCK_AFTER - timedelta(seconds=1)
    runner = FakeRunner(engine)
    drain(engine, runner, ticks=3)
    assert runner.ran == []
    assert step_states(engine, run_id) == {"a": FAILURE}
    assert run_status(engine, run_id) == FAILURE


class ErroringBaseRunner(BaseRunner):
    """A runner whose script always fails, so the invocation ends as ERROR."""

    def run(self, request):
        return RunResult(status="ERROR", logs="boom", error="Exited with code 1")


class CapturingBaseRunner(BaseRunner):
    """Records the env each script is given, and reports success."""

    def __init__(self):
        self.envs = []

    def run(self, request):
        self.envs.append(request.env)
        return RunResult(status="SUCCESS", logs="", result=None, error=None)


def test_step_gets_a_token_for_the_user_who_started_the_run(engine, monkeypatch):
    """A step runs with the API URL and a token that acts as the run's user."""
    monkeypatch.setattr("kangaroo.orchestrator.settings.api_public_url", "http://api")
    user = {"sub": "user-1", "email": "owner@example.com", "name": "owner"}
    queue_run = queue(engine, {"a": ([], [])}, started_by=user)
    runner = CapturingBaseRunner()
    drain(engine, FunctionStepRunner(engine, runner))

    [env] = runner.envs
    assert env["KANGAROO_API_URL"] == "http://api"
    assert verify_impersonation_token(env["KANGAROO_TOKEN"])["email"] == (
        "owner@example.com"
    )
    assert step_states(engine, queue_run) == {"a": SUCCESS}


def test_step_of_a_run_without_a_user_gets_no_token(engine, monkeypatch):
    """A run with no recorded user gives its steps the URL only, not a token."""
    monkeypatch.setattr("kangaroo.orchestrator.settings.api_public_url", "http://api")
    queue(engine, {"a": ([], [])})
    runner = CapturingBaseRunner()
    drain(engine, FunctionStepRunner(engine, runner))

    [env] = runner.envs
    assert env == {"KANGAROO_API_URL": "http://api"}


def test_function_step_runner_maps_error_invocation_to_failure(engine):
    """An invocation that ends as ERROR becomes a FAILURE step, which the API accepts."""
    run_id = queue(engine, {"broken": ([], [])})
    drain(engine, FunctionStepRunner(engine, ErroringBaseRunner()))
    assert step_states(engine, run_id) == {"broken": FAILURE}
    assert run_status(engine, run_id) == FAILURE
