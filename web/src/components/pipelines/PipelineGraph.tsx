import { Background, Controls, ReactFlow } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useMemo } from "react";
import { stepsToGraph, type Steps } from "./graph";
import { StepNode } from "./StepNode";

const nodeTypes = { step: StepNode };

// Read-only view of a definition with each step's status, used by the run page.
// It derives everything from props, so it never writes state back.
export function PipelineGraph({
  steps,
  statuses,
}: {
  steps: Steps;
  statuses: Record<string, string>;
}) {
  const graph = useMemo(() => stepsToGraph(steps, statuses), [steps, statuses]);

  return (
    <div className="h-[480px] w-full rounded border border-border">
      <ReactFlow
        nodes={graph.nodes}
        edges={graph.edges}
        nodeTypes={nodeTypes}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        fitView
      >
        <Background />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}
