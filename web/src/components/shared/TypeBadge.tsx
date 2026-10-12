import type { TypeRef } from "../../lib/work-items";
import type { TypeLevel } from "../../lib/workflow";

// Colours follow the type level, so any type name gets the right colour
const COLOURS: Record<TypeLevel, string> = {
  standard: "bg-gray-100 text-gray-800",
  subtask: "bg-purple-100 text-purple-800",
};

export function TypeBadge({ type }: { type: TypeRef }) {
  return (
    <span
      className={`rounded px-2 py-0.5 text-xs font-medium ${COLOURS[type.level]}`}
    >
      {type.name}
    </span>
  );
}
