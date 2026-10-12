import type { StatusRef } from "../../lib/work-items";
import type { StatusCategory } from "../../lib/workflow";

// Colours follow the status category, so any status name gets the right colour
const COLOURS: Record<StatusCategory, string> = {
  todo: "bg-yellow-100 text-yellow-800",
  in_progress: "bg-blue-100 text-blue-800",
  done: "bg-green-100 text-green-800",
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
