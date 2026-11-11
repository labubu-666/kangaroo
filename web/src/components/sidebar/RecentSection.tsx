import { Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  clearLegacyRecent,
  useClearRecent,
  useRecentEntries,
  type RecentType,
} from "../../lib/recent";
import { SidebarSection } from "./SidebarSection";
import { useSidebar } from "./SidebarContext";

const ICON_PATHS: Record<RecentType, string> = {
  project:
    "M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z",
  board: "M4 4h4v16H4zM10 4h4v10h-4zM16 4h4v13h-4z",
  "project-tab":
    "M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z",
  function: "M16 18l6-6-6-6M8 6l-6 6 6 6",
  pipeline: "M4 6h5v5H4zM15 13h5v5h-5zM9 8.5h3a3 3 0 0 1 3 3v0",
  article: "M6 2h9l5 5v15H6zM14 2v6h6M9 13h6M9 17h6",
  calendar: "M3 4h18v18H3zM16 2v4M8 2v4M3 10h18",
  "knowledge-base":
    "M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20",
  "work-item":
    "M9 11l3 3L22 4M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11",
};

function RecentIcon({ type }: { type: RecentType }) {
  return (
    <svg
      width={16}
      height={16}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className="shrink-0"
    >
      <path d={ICON_PATHS[type]} />
    </svg>
  );
}

function ClockIcon() {
  return (
    <svg
      width={16}
      height={16}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className="shrink-0"
    >
      <circle cx="12" cy="12" r="10" />
      <path d="M12 6v6l4 2" />
    </svg>
  );
}

const DEBOUNCE_MS = 250;

export function RecentSection() {
  const [text, setText] = useState("");
  const [term, setTerm] = useState("");
  const entries = useRecentEntries(term);
  const clear = useClearRecent();
  const { setMobileOpen } = useSidebar();

  useEffect(() => {
    clearLegacyRecent();
  }, []);

  // Wait for typing to pause before searching
  useEffect(() => {
    const timer = setTimeout(() => setTerm(text.trim()), DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [text]);

  return (
    <SidebarSection
      icon={<ClockIcon />}
      label="Recent"
      storageKey="kangaroo-sidebar-recent"
    >
      <div className="flex items-center justify-between gap-2">
        <input
          type="search"
          aria-label="Search recent"
          placeholder="Search recent"
          value={text}
          onChange={(e) => setText(e.target.value)}
          className="min-w-0 flex-1 rounded border border-border-strong px-2 py-1 text-sm"
        />
        {entries.length > 0 && (
          <button
            type="button"
            onClick={() => clear.mutate()}
            disabled={clear.isPending}
            className="text-sm text-fg-muted hover:text-fg"
          >
            Clear
          </button>
        )}
      </div>
      {entries.length === 0 ? (
        <p className="px-2 text-sm text-fg-muted">
          {term ? "No matches" : "Nothing yet"}
        </p>
      ) : (
        <>
          <ul className="flex flex-col gap-1">
            {entries.map((entry) => (
              <li key={`${entry.type}-${entry.id}`}>
                <Link
                  to={entry.to}
                  params={entry.params}
                  search={"search" in entry ? entry.search : undefined}
                  title={entry.title}
                  onClick={() => setMobileOpen(false)}
                  activeProps={{ className: "text-primary" }}
                  className="flex min-w-0 items-center gap-2 rounded px-2 py-1.5 hover:bg-surface-strong"
                >
                  <RecentIcon type={entry.type} />
                  <span className="flex min-w-0 flex-col">
                    <span className="truncate">{entry.title}</span>
                    {"parent" in entry && entry.parent && (
                      <span className="truncate text-xs text-fg-muted">
                        {entry.parent}
                      </span>
                    )}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </>
      )}
    </SidebarSection>
  );
}
