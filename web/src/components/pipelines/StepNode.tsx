import { Handle, Position, type NodeProps } from "@xyflow/react";
import { NODE_HEIGHT, NODE_WIDTH } from "./graph";

// Node colours come from the step status. Green, yellow and amber are status
// colours, so each has a dark variant as AGENTS.md asks.
const STATUS_CLASS: Record<string, string> = {
  RUNNING: "border-amber-500 bg-amber-50 dark:bg-amber-950",
  SUCCESS: "border-green-600 bg-green-50 dark:bg-green-950",
  FAILURE: "border-danger bg-danger-subtle",
  SKIPPED: "border-border bg-surface-muted text-fg-muted",
  PENDING: "border-border bg-surface",
};

export function StepNode({ data }: NodeProps) {
  const status = (data.status as string | null) ?? null;
  const classes = status ? STATUS_CLASS[status] : "border-border bg-surface";
  const onDelete = data.onDelete as (() => void) | undefined;
  return (
    <div
      style={{ width: NODE_WIDTH, height: NODE_HEIGHT }}
      className={`relative flex flex-col justify-center rounded border-2 px-3 ${classes}`}
    >
      <Handle type="target" position={Position.Left} />
      <span className="truncate pr-6 font-semibold">
        {data.label as string}
      </span>
      {status && <span className="text-xs text-fg-muted">{status}</span>}
      {onDelete && (
        <button
          type="button"
          aria-label={`Delete ${data.label as string}`}
          onClick={onDelete}
          className="nodrag absolute right-1 top-1 flex h-5 w-5 items-center justify-center rounded text-fg-muted hover:bg-surface-strong hover:text-danger"
        >
          ×
        </button>
      )}
      <Handle
        id="success"
        type="source"
        position={Position.Right}
        style={{ top: "35%" }}
        className="!bg-green-600"
      />
      <Handle
        id="failure"
        type="source"
        position={Position.Right}
        style={{ top: "70%" }}
        className="!bg-danger"
      />
    </div>
  );
}
