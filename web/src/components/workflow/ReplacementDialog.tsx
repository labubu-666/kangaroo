import { useState } from "react";

interface ReplacementOption {
  id: string;
  name: string;
}

// Asks which item should take over the work items of a status or type that is
// being deleted. The delete button stays disabled until one is chosen.
export function ReplacementDialog({
  kind,
  name,
  count,
  options,
  busy,
  error,
  onConfirm,
  onCancel,
}: {
  kind: "status" | "type";
  name: string;
  count: number;
  options: ReplacementOption[];
  busy: boolean;
  error: string | null;
  onConfirm: (replacementId: string) => void;
  onCancel: () => void;
}) {
  const [replacementId, setReplacementId] = useState("");
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="replacement-title"
      className="space-y-4 rounded border border-red-200 bg-white p-4 shadow"
    >
      <h3 id="replacement-title" className="font-semibold">
        Delete {kind} “{name}”?
      </h3>
      <p className="text-sm text-gray-700">
        {count} work {count === 1 ? "item uses" : "items use"} this {kind}.
        Choose the {kind} they should move to.
      </p>
      <label className="block text-sm font-medium" htmlFor="replacement">
        Replacement {kind}
      </label>
      <select
        id="replacement"
        value={replacementId}
        disabled={busy}
        onChange={(e) => setReplacementId(e.target.value)}
        className="w-full rounded border border-gray-300 px-3 py-2"
      >
        <option value="">Choose a {kind}…</option>
        {options.map((option) => (
          <option key={option.id} value={option.id}>
            {option.name}
          </option>
        ))}
      </select>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="flex gap-3">
        <button
          type="button"
          disabled={busy || !replacementId}
          onClick={() => onConfirm(replacementId)}
          className="rounded bg-red-600 px-4 py-2 font-medium text-white hover:bg-red-700 disabled:bg-gray-400"
        >
          Delete and move items
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="rounded border border-gray-300 px-4 py-2 font-medium hover:bg-gray-50"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
