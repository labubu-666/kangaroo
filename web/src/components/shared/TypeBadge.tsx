import type { TypeRef } from "../../lib/work-items";

const TONES: Record<string, string> = {
  story: "bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300",
  bug: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300",
  task: "bg-primary-subtle text-primary",
};

export function TypeBadge({ type }: { type: TypeRef }) {
  const tone = TONES[type.name.toLowerCase()] ?? "bg-surface-strong text-fg";
  return (
    <span className={`rounded px-2 py-0.5 text-xs font-medium ${tone}`}>
      {type.name}
    </span>
  );
}
