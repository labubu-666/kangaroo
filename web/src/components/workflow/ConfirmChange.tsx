// Asks before a status change that affects other things: a rename that breaks
// saved board filters, or a category change that moves work items.
export function ConfirmChange({
  title,
  lines,
  busy,
  onConfirm,
  onCancel,
}: {
  title: string;
  lines: string[];
  busy: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-change-title"
      className="space-y-3 rounded border border-yellow-300 bg-yellow-50 p-4"
    >
      <h3 id="confirm-change-title" className="font-semibold">
        {title}
      </h3>
      <ul className="list-disc space-y-1 pl-5 text-sm text-gray-800">
        {lines.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>
      <div className="flex gap-3">
        <button
          type="button"
          disabled={busy}
          onClick={onConfirm}
          className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:bg-gray-400"
        >
          Continue
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
