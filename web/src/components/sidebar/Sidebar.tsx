import type { ReactNode } from "react";
import { useDismiss } from "../../lib/use-dismiss";
import { useSidebar } from "./SidebarContext";

// The shared shell: a left column on desktop, a drawer on mobile.
// Sections are passed as children.
export function Sidebar({ children }: { children: ReactNode }) {
  const { collapsed, toggleCollapsed, mobileOpen, setMobileOpen } =
    useSidebar();
  const asideRef = useDismiss<HTMLElement>(mobileOpen, () =>
    setMobileOpen(false),
  );

  return (
    <>
      {mobileOpen && (
        <div
          aria-hidden="true"
          onClick={() => setMobileOpen(false)}
          className="fixed inset-0 z-20 bg-black/40 md:hidden"
        />
      )}
      <aside
        ref={asideRef}
        aria-label="Sidebar"
        className={`flex-col gap-3 overflow-y-auto border-r border-border bg-sidebar p-3 md:static md:flex md:shrink-0 ${
          mobileOpen
            ? "fixed inset-y-0 left-0 z-30 flex w-56"
            : "hidden md:flex"
        } ${collapsed ? "md:w-14" : "md:w-56"}`}
      >
        <div className="flex justify-end">
          <button
            type="button"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-expanded={!collapsed}
            onClick={toggleCollapsed}
            className="hidden h-7 w-7 items-center justify-center rounded hover:bg-surface-strong md:flex"
          >
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
            >
              <path d={collapsed ? "M9 18l6-6-6-6" : "M15 18l-6-6 6-6"} />
            </svg>
          </button>
        </div>
        {children}
      </aside>
    </>
  );
}
