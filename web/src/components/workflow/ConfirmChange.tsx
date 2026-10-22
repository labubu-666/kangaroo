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
      className="space-y-3 rounded border border-yellow-300 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-950 p-4"
    >
      <h3 id="confirm-change-title" className="font-semibold">
        {title}
      </h3>
      <ul className="list-disc space-y-1 pl-5 text-sm text-fg">
        {lines.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>
      <div className="flex gap-3">
        <button
          type="button"
          disabled={busy}
          onClick={onConfirm}
          className="rounded bg-primary px-4 py-2 font-medium text-on-primary hover:bg-primary-hover disabled:bg-fg-disabled"
        >
          Continue
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="rounded border border-border-strong px-4 py-2 font-medium hover:bg-surface-muted"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
