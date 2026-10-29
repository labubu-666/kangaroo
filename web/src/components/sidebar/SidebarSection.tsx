import { useId, useState, type ReactNode } from "react";
import { useSidebar } from "./SidebarContext";

interface SidebarSectionProps {
  icon: ReactNode;
  label: string;
  storageKey: string;
  children: ReactNode;
}

// Sections start open. Minimised, only the icon shows and it opens the section.
export function SidebarSection({
  icon,
  label,
  storageKey,
  children,
}: SidebarSectionProps) {
  const { collapsed, expand } = useSidebar();
  const contentId = useId();
  const [open, setOpen] = useState(
    () => localStorage.getItem(storageKey) !== "closed",
  );

  const setSectionOpen = (next: boolean) => {
    if (next) localStorage.removeItem(storageKey);
    else localStorage.setItem(storageKey, "closed");
    setOpen(next);
  };

  return (
    <section className="flex flex-col gap-1">
      <button
        type="button"
        aria-label={label}
        title={label}
        onClick={() => {
          expand();
          setSectionOpen(true);
        }}
        className={`${collapsed ? "hidden md:flex" : "hidden"} h-8 w-8 items-center justify-center rounded text-fg-secondary hover:bg-surface-strong`}
      >
        {icon}
      </button>
      <button
        type="button"
        aria-expanded={open}
        aria-controls={contentId}
        onClick={() => setSectionOpen(!open)}
        className={`${collapsed ? "md:hidden" : "flex"} items-center gap-2 rounded px-2 py-1.5 text-sm font-semibold uppercase text-fg-muted hover:text-fg`}
      >
        {icon}
        <span className="flex-1 text-left">{label}</span>
        <svg
          width={14}
          height={14}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
          className={`shrink-0 transition-transform ${open ? "" : "-rotate-90"}`}
        >
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>
      <div
        id={contentId}
        className={`${open ? "" : "hidden"} ${collapsed ? "md:hidden" : ""} flex flex-col gap-1 pl-2`}
      >
        {children}
      </div>
    </section>
  );
}
