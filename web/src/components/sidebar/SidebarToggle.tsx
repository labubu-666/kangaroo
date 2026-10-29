import { useSidebar } from "./SidebarContext";

// Mobile only: opens the drawer. On desktop the sidebar is always visible.
export function SidebarToggle() {
  const { mobileOpen, setMobileOpen } = useSidebar();
  return (
    <div className="px-4 pt-4 md:hidden">
      <button
        type="button"
        aria-label="Open sidebar"
        aria-expanded={mobileOpen}
        onClick={() => setMobileOpen(true)}
        className="flex h-8 items-center rounded border border-border-strong px-3 text-sm font-medium hover:bg-surface-strong"
      >
        Sidebar
      </button>
    </div>
  );
}
