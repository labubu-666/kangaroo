import {
  addEdge,
  Background,
  Controls,
  ReactFlow,
  useEdgesState,
  useNodesState,
  type Connection,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
} from "react";
import {
  graphToSteps,
  NODE_HEIGHT,
  stepsToGraph,
  uniqueStepName,
  type Steps,
} from "./graph";
import { StepNode } from "./StepNode";

const nodeTypes = { step: StepNode };

export interface PipelineEditorHandle {
  addStep: (functionId: string, functionName: string) => void;
}

// The canvas owns its nodes and edges. It takes the starting definition once,
// and reports each change to the parent. It never copies props back in, so the
// parent's update cannot trigger another copy.
export const PipelineEditor = forwardRef<
  PipelineEditorHandle,
  {
    initialSteps: Steps;
    disabled: boolean;
    onChange: (steps: Steps) => void;
  }
>(function PipelineEditor({ initialSteps, disabled, onChange }, ref) {
  const initial = useRef(stepsToGraph(initialSteps)).current;
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>(initial.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>(initial.edges);

  useImperativeHandle(
    ref,
    () => ({
      addStep: (functionId: string, functionName: string) => {
        setNodes((current) => {
          const name = uniqueStepName(
            new Set(current.map((node) => node.id)),
            functionName,
          );
          const position = {
            x: 0,
            y: current.length * (NODE_HEIGHT + 40),
          };
          return [
            ...current,
            {
              id: name,
              type: "step",
              position,
              data: { label: name, functionId, status: null },
            },
          ];
        });
      },
    }),
    [setNodes],
  );

  const onConnect = useCallback(
    (connection: Connection) => {
      if (disabled || !connection.source || !connection.target) return;
      const outcome =
        connection.sourceHandle === "failure" ? "failure" : "success";
      setEdges((current) =>
        addEdge(
          {
            ...connection,
            id: `${outcome}:${connection.source}->${connection.target}`,
            data: { outcome },
          },
          current,
        ),
      );
    },
    [disabled, setEdges],
  );

  // Removing a step also removes the edges that touch it, so no edge is left
  // pointing at a step that is gone.
  const deleteStep = useCallback(
    (name: string) => {
      if (disabled) return;
      setNodes((current) => current.filter((node) => node.id !== name));
      setEdges((current) =>
        current.filter((edge) => edge.source !== name && edge.target !== name),
      );
    },
    [disabled, setNodes, setEdges],
  );

  // The delete callback goes in node data, so it has to follow the latest state.
  const displayNodes = useMemo(
    () =>
      nodes.map((node) => ({
        ...node,
        data: { ...node.data, onDelete: () => deleteStep(node.id) },
      })),
    [nodes, deleteStep],
  );

  // Edges and nodes change together, so reporting from the same render is safe.
  useEffect(() => {
    onChange(graphToSteps(nodes, edges));
  }, [nodes, edges, onChange]);

  return (
    <div className="h-[480px] w-full rounded border border-border">
      <ReactFlow
        nodes={displayNodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={disabled ? undefined : onNodesChange}
        onEdgesChange={disabled ? undefined : onEdgesChange}
        onConnect={onConnect}
        nodesDraggable={!disabled}
        nodesConnectable={!disabled}
        elementsSelectable={!disabled}
        fitView
      >
        <Background />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
});
