import type { Invocation } from "../../lib/invocations";

export const STATUS_TEXT: Record<Invocation["status"], string> = {
  RUNNING: "text-blue-700",
  SUCCESS: "text-green-700",
  ERROR: "text-red-700",
};

export function RunOutput({ result }: { result: Invocation }) {
  return (
    <div
      role="region"
      aria-label="Run output"
      className="space-y-3 rounded border border-gray-200 p-4"
    >
      <p className={`font-semibold ${STATUS_TEXT[result.status]}`}>
        {result.status}
      </p>
      {result.error && <p className="text-sm text-red-700">{result.error}</p>}
      <div>
        <h3 className="mb-1 font-medium text-gray-700">Logs</h3>
        <pre className="overflow-x-auto whitespace-pre-wrap rounded bg-gray-50 p-3 font-mono text-sm">
          {result.logs || "(empty)"}
        </pre>
      </div>
      <div>
        <h3 className="mb-1 font-medium text-gray-700">Result</h3>
        <pre className="overflow-x-auto whitespace-pre-wrap rounded bg-gray-50 p-3 font-mono text-sm">
          {result.result === null
            ? "null"
            : JSON.stringify(result.result, null, 2)}
        </pre>
      </div>
    </div>
  );
}
