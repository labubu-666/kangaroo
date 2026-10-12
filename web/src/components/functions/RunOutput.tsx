import type { RunResult } from "../../lib/functions";

export function RunOutput({ result }: { result: RunResult }) {
  const succeeded = result.exit_code === 0;
  return (
    <div
      role="region"
      aria-label="Run output"
      className="space-y-3 rounded border border-gray-200 p-4"
    >
      <p
        className={`font-semibold ${succeeded ? "text-green-700" : "text-red-700"}`}
      >
        Exit code {result.exit_code}
      </p>
      <div>
        <h3 className="mb-1 font-medium text-gray-700">stdout</h3>
        <pre className="overflow-x-auto whitespace-pre-wrap rounded bg-gray-50 p-3 font-mono text-sm">
          {result.stdout || "(empty)"}
        </pre>
      </div>
      <div>
        <h3 className="mb-1 font-medium text-gray-700">stderr</h3>
        <pre className="overflow-x-auto whitespace-pre-wrap rounded bg-gray-50 p-3 font-mono text-sm">
          {result.stderr || "(empty)"}
        </pre>
      </div>
    </div>
  );
}
