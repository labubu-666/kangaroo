import type { Invocation } from "../../lib/invocations";

export const STATUS_TEXT: Record<Invocation["status"], string> = {
  RUNNING: "text-primary-hover",
  SUCCESS: "text-green-700 dark:text-green-400",
  ERROR: "text-danger-hover",
};

export function RunOutput({ result }: { result: Invocation }) {
  return (
    <div
      role="region"
      aria-label="Run output"
      className="space-y-3 rounded border border-border p-4"
    >
      <p className={`font-semibold ${STATUS_TEXT[result.status]}`}>
        {result.status}
      </p>
      {result.error && (
        <p className="text-sm text-danger-hover">{result.error}</p>
      )}
      <div>
        <h3 className="mb-1 font-medium text-fg-secondary">Logs</h3>
        <pre className="overflow-x-auto whitespace-pre-wrap rounded bg-surface-muted p-3 font-mono text-sm">
          {result.logs || "(empty)"}
        </pre>
      </div>
      <div>
        <h3 className="mb-1 font-medium text-fg-secondary">Result</h3>
        <pre className="overflow-x-auto whitespace-pre-wrap rounded bg-surface-muted p-3 font-mono text-sm">
          {result.result === null
            ? "null"
            : JSON.stringify(result.result, null, 2)}
        </pre>
      </div>
    </div>
  );
}
