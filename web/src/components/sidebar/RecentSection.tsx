import { Link } from "@tanstack/react-router";
import {
  clearRecent,
  useRecentEntries,
  type RecentType,
} from "../../lib/recent";
import { SidebarSection } from "./SidebarSection";
import { useSidebar } from "./SidebarContext";

const ICON_PATHS: Record<RecentType, string> = {
  project:
    "M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z",
  board: "M4 4h4v16H4zM10 4h4v10h-4zM16 4h4v13h-4z",
  function: "M16 18l6-6-6-6M8 6l-6 6 6 6",
  article: "M6 2h9l5 5v15H6zM14 2v6h6M9 13h6M9 17h6",
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

export function RecentSection() {
  const entries = useRecentEntries();
  const { setMobileOpen } = useSidebar();

  return (
    <SidebarSection
      icon={<ClockIcon />}
      label="Recent"
      storageKey="kangaroo-sidebar-recent"
    >
      {entries.length === 0 ? (
        <p className="px-2 text-sm text-fg-muted">Nothing yet</p>
      ) : (
        <>
          <div className="flex justify-end">
            <button
              type="button"
              onClick={clearRecent}
              className="text-sm text-fg-muted hover:text-fg"
            >
              Clear
            </button>
          </div>
          <ul className="flex flex-col gap-1">
            {entries.map((entry) => (
              <li key={`${entry.type}-${entry.id}`}>
                <Link
                  to={entry.to}
                  params={entry.params}
                  title={entry.title}
                  onClick={() => setMobileOpen(false)}
                  activeProps={{ className: "text-primary" }}
                  className="flex min-w-0 items-center gap-2 rounded px-2 py-1.5 hover:bg-surface-strong"
                >
                  <RecentIcon type={entry.type} />
                  <span className="truncate">{entry.title}</span>
                </Link>
              </li>
            ))}
          </ul>
        </>
      )}
    </SidebarSection>
  );
}
