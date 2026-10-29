import type { TypeRef } from "../../lib/work-items";

export function TypeBadge({ type }: { type: TypeRef }) {
  return (
    <span className="rounded bg-surface-strong px-2 py-0.5 text-xs font-medium text-fg">
      {type.name}
    </span>
  );
}
