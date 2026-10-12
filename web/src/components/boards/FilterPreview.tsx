import { CopyFilter } from "../shared/CopyFilter";

// Shows a board's filter as code with a copy button
export function FilterPreview({ filter }: { filter: string }) {
  return (
    <div className="relative">
      <pre className="select-text overflow-auto whitespace-pre-wrap break-words rounded border border-gray-200 bg-gray-50 p-3 pr-12 font-mono text-sm text-gray-700">
        {filter}
      </pre>
      <div className="absolute right-2 top-2">
        <CopyFilter filter={filter} />
      </div>
    </div>
  );
}
