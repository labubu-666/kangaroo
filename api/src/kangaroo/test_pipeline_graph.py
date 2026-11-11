from uuid import uuid4

import pytest

from kangaroo.pipeline_graph import (
    FAILURE,
    PENDING,
    SKIPPED,
    SUCCESS,
    InvalidPipelineError,
    build_graph,
    plan_next,
)
from kangaroo.schemas import PipelineStep


def step(on_success=(), on_failure=()):
    return PipelineStep(
        function_id=uuid4(), on_success=list(on_success), on_failure=list(on_failure)
    )


def all_pending(graph):
    return {name: PENDING for name in graph.nodes}


def test_first_step_is_ready_and_others_wait():
    graph = build_graph({"a": step(["b"]), "b": step()})
    assert plan_next(graph, all_pending(graph)) == (["a"], [])


def test_success_runs_success_branch_and_skips_failure_branch():
    graph = build_graph({"a": step(["b"], ["c"]), "b": step(), "c": step()})
    states = {"a": SUCCESS, "b": PENDING, "c": PENDING}
    assert plan_next(graph, states) == (["b"], ["c"])


def test_failure_runs_failure_branch_and_skips_success_branch():
    graph = build_graph({"a": step(["b"], ["c"]), "b": step(), "c": step()})
    states = {"a": FAILURE, "b": PENDING, "c": PENDING}
    assert plan_next(graph, states) == (["c"], ["b"])


def test_merge_waits_for_every_parent_to_finish():
    graph = build_graph(
        {"s": step(["a", "b"]), "a": step(["c"]), "b": step(["c"]), "c": step()}
    )
    states = {"s": SUCCESS, "a": SUCCESS, "b": PENDING, "c": PENDING}
    assert plan_next(graph, states) == (["b"], [])


def test_merge_runs_when_all_parents_succeed():
    graph = build_graph({"a": step(["c"]), "b": step(["c"]), "c": step()})
    states = {"a": SUCCESS, "b": SUCCESS, "c": PENDING}
    assert plan_next(graph, states) == (["c"], [])


def test_merge_runs_when_one_parent_branch_is_live():
    graph = build_graph({"a": step(["c"]), "b": step(on_failure=["c"]), "c": step()})
    states = {"a": SUCCESS, "b": SUCCESS, "c": PENDING}
    assert plan_next(graph, states) == (["c"], [])


def test_merge_is_skipped_when_every_live_edge_is_dead():
    graph = build_graph({"a": step(["c"]), "b": step(on_failure=["c"]), "c": step()})
    states = {"a": FAILURE, "b": SUCCESS, "c": PENDING}
    assert plan_next(graph, states) == ([], ["c"])


def test_skip_passes_on_to_descendants():
    graph = build_graph(
        {"a": step(["b"], ["c"]), "b": step(["d"]), "c": step(), "d": step()}
    )
    states = {"a": FAILURE, "b": SKIPPED, "c": PENDING, "d": PENDING}
    assert plan_next(graph, states) == (["c"], ["d"])


def test_unknown_reference_is_rejected():
    with pytest.raises(InvalidPipelineError):
        build_graph({"a": step(["missing"])})


def test_cycle_is_rejected():
    with pytest.raises(InvalidPipelineError):
        build_graph({"a": step(["b"]), "b": step(["a"])})
