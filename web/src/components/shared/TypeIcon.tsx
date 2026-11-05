import type { ReactNode } from "react";
import type { TypeRef } from "../../lib/work-items";

const ICONS: Record<string, { fill: string; glyph: ReactNode }> = {
  story: {
    fill: "#36B37E",
    glyph: (
      <path d="M5 3.5h6v9L8 10l-3 2.5z" fill="white" strokeLinejoin="round" />
    ),
  },
  bug: {
    fill: "#E5493A",
    glyph: <circle cx="8" cy="8" r="4.5" fill="white" />,
  },
  task: {
    fill: "#4BADE8",
    glyph: (
      <path
        d="M4.5 8.5l2.25 2.25L11.5 5.5"
        fill="none"
        stroke="white"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    ),
  },
};

export function TypeIcon({ type }: { type: TypeRef }) {
  const label = type.name;
  const { fill, glyph } = ICONS[type.name.toLowerCase()] ?? ICONS.task;
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
      <rect width="16" height="16" rx="2" fill={fill} />
      {glyph}
    </svg>
  );
}
