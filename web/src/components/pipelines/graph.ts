import type { Edge, Node } from "@xyflow/react";
import type { PipelineStep } from "../../lib/pipelines";

export type Steps = Record<string, PipelineStep>;

export const NODE_WIDTH = 200;
export const NODE_HEIGHT = 60;
const COLUMN_GAP = 80;
const ROW_GAP = 40;

export type Outcome = "success" | "failure";

// Edge IDs encode the outcome and the two ends, so a deleted edge maps back cleanly.
export function edgeId(from: string, to: string, outcome: Outcome): string {
  return `${outcome}:${from}->${to}`;
}

// Steps are keyed by name, so a function added twice gets "name", then "name-2"...
export function uniqueStepName(taken: Set<string>, base: string): string {
  if (!taken.has(base)) return base;
  let n = 2;
  while (taken.has(`${base}-${n}`)) n += 1;
  return `${base}-${n}`;
}

// Column = longest path from a root. The layout depends only on the graph,
// so the saved definition stores no positions.
export function layoutDepths(steps: Steps): Map<string, number> {
  const parents = new Map<string, string[]>();
  for (const name of Object.keys(steps)) parents.set(name, []);
  for (const [name, step] of Object.entries(steps)) {
    for (const child of [...step.on_success, ...step.on_failure]) {
      parents.get(child)?.push(name);
    }
  }
  const depth = new Map<string, number>();
  const visit = (name: string, trail: Set<string>): number => {
    const known = depth.get(name);
    if (known !== undefined) return known;
    // The API rejects cycles, so this guard only stops an unsaved bad draft.
    if (trail.has(name)) return 0;
    trail.add(name);
    const parentDepths = (parents.get(name) ?? []).map((p) => visit(p, trail));
    trail.delete(name);
    const value = parentDepths.length ? Math.max(...parentDepths) + 1 : 0;
    depth.set(name, value);
    return value;
  };
  for (const name of Object.keys(steps)) visit(name, new Set());
  return depth;
}

export function stepsToGraph(
  steps: Steps,
  statuses: Record<string, string> = {},
): { nodes: Node[]; edges: Edge[] } {
  const depth = layoutDepths(steps);
  const rowInColumn = new Map<number, number>();
  const nodes: Node[] = Object.entries(steps).map(([name, step]) => {
    const column = depth.get(name) ?? 0;
    const row = rowInColumn.get(column) ?? 0;
    rowInColumn.set(column, row + 1);
    return {
      id: name,
      type: "step",
      position: {
        x: column * (NODE_WIDTH + COLUMN_GAP),
        y: row * (NODE_HEIGHT + ROW_GAP),
      },
      data: {
        label: name,
        functionId: step.function_id,
        status: statuses[name] ?? null,
      },
    };
  });
  const edges: Edge[] = [];
  for (const [name, step] of Object.entries(steps)) {
    for (const target of step.on_success) {
      edges.push({
        id: edgeId(name, target, "success"),
        source: name,
        target,
        sourceHandle: "success",
        data: { outcome: "success" },
      });
    }
    for (const target of step.on_failure) {
      edges.push({
        id: edgeId(name, target, "failure"),
        source: name,
        target,
        sourceHandle: "failure",
        data: { outcome: "failure" },
      });
    }
  }
  return { nodes, edges };
}

export function graphToSteps(nodes: Node[], edges: Edge[]): Steps {
  const steps: Steps = {};
  for (const node of nodes) {
    steps[node.id] = {
      function_id: node.data.functionId as string,
      on_success: [],
      on_failure: [],
    };
  }
  for (const edge of edges) {
    const key = edge.sourceHandle === "failure" ? "on_failure" : "on_success";
    steps[edge.source]?.[key].push(edge.target);
  }
  return steps;
}
