"""Pipeline graph rules: which steps to run next, and which to skip.

A pipeline is a map from step name to its ``on_success`` and ``on_failure``
references. A step runs only when one of its parents finished along an edge
that leads to it, so a branch that was not taken never runs.
"""

from collections.abc import Mapping

import networkx as nx

from kangaroo.schemas import PipelineStep

PENDING = "PENDING"
RUNNING = "RUNNING"
SUCCESS = "SUCCESS"
FAILURE = "FAILURE"
SKIPPED = "SKIPPED"
FINISHED = {SUCCESS, FAILURE, SKIPPED}


class InvalidPipelineError(ValueError):
    """The pipeline refers to a step that is not defined, or has a cycle."""


def build_graph(steps: Mapping[str, PipelineStep]) -> nx.DiGraph:
    """Return the step graph. Raises InvalidPipelineError on unknown refs or cycles."""
    graph = nx.DiGraph()
    graph.add_nodes_from(steps)
    for name, step in steps.items():
        for target in step.on_success:
            graph.add_edge(name, target, outcome=SUCCESS)
        for target in step.on_failure:
            graph.add_edge(name, target, outcome=FAILURE)
    if any(target not in steps for _, target in graph.edges):
        raise InvalidPipelineError("Pipeline refers to a step that is not defined")
    if not nx.is_directed_acyclic_graph(graph):
        raise InvalidPipelineError("Pipeline has a cycle")
    return graph


def plan_next(
    graph: nx.DiGraph, states: Mapping[str, str]
) -> tuple[list[str], list[str]]:
    """Return (ready, skipped): steps that can run now, and steps that never will.

    A PENDING step waits until all its parents have finished. Then it is ready if
    any parent took a live edge into it, and skipped otherwise. A step with no
    parents is always ready.
    """
    ready: list[str] = []
    skipped: list[str] = []
    for name in graph.nodes:
        if states.get(name) != PENDING:
            continue
        parents = list(graph.predecessors(name))
        if not all(states.get(parent) in FINISHED for parent in parents):
            continue
        live = any(_is_live(graph, parent, name, states[parent]) for parent in parents)
        (ready if live or not parents else skipped).append(name)
    return ready, skipped


def _is_live(graph: nx.DiGraph, parent: str, child: str, parent_state: str) -> bool:
    """An edge is live only if the parent's outcome matches the edge's outcome."""
    return graph.edges[parent, child]["outcome"] == parent_state
