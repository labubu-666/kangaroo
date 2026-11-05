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
    glyph: (
      <g fill="white" stroke="white" strokeLinecap="round">
        <circle cx="8" cy="4" r="1.6" stroke="none" />
        <rect x="5" y="6.25" width="6" height="7.5" rx="3" stroke="none" />
        <path d="M6.5 2.5L5.25 1.25M9.5 2.5L10.75 1.25" strokeWidth={1} />
        <path
          d="M4.75 8.25H2.5M4.75 11H2.5M11.25 8.25H13.5M11.25 11H13.5"
          strokeWidth={1}
        />
        <path d="M8 6.75V13.25" stroke="#E5493A" strokeWidth={0.8} />
      </g>
    ),
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
