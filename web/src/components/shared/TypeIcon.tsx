import type { TypeRef } from "../../lib/work-items";

export function TypeIcon({ type }: { type: TypeRef }) {
  const label = type.name;
  const isSubtask = type.level === "subtask";
  return (
    <svg
      role="img"
      aria-label={label}
      width={16}
      height={16}
      viewBox="0 0 16 16"
      className="flex-none"
    >
      <title>{label}</title>
      <rect width="16" height="16" rx="2" fill="#4BADE8" />
      {isSubtask ? (
        <g fill="white">
          <rect x="4" y="4" width="8" height="3" rx="0.5" />
          <rect x="4" y="9" width="8" height="3" rx="0.5" />
        </g>
      ) : (
        <path
          d="M4.5 8.5l2.25 2.25L11.5 5.5"
          fill="none"
          stroke="white"
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      )}
    </svg>
  );
}
