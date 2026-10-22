import type { StatusRef } from "../../lib/work-items";
import type { StatusCategory } from "../../lib/workflow";

// Colours follow the status category, so any status name gets the right colour
const COLOURS: Record<StatusCategory, string> = {
  todo: "bg-yellow-100 dark:bg-yellow-900/40 text-yellow-800 dark:text-yellow-200",
  in_progress:
    "bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-200",
  done: "bg-green-100 dark:bg-green-900/40 text-green-800 dark:text-green-200",
};

export function StatusBadge({ status }: { status: StatusRef }) {
  return (
    <span
      className={`rounded-full px-3 py-1 text-sm font-medium ${COLOURS[status.category]}`}
    >
      {status.name}
    </span>
  );
}
