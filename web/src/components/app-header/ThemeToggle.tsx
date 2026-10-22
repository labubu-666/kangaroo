import { useId, useState } from "react";
import { useDismiss } from "../../lib/use-dismiss";
import { useTheme, type ThemeChoice } from "../../lib/theme";

const OPTIONS: { value: ThemeChoice; label: string }[] = [
  { value: "light", label: "Light" },
  { value: "system", label: "System" },
  { value: "dark", label: "Dark" },
];

function ThemeIcon({ value }: { value: ThemeChoice }) {
  const common = {
    width: 16,
    height: 16,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 2,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
  };
  if (value === "light") {
    return (
      <svg {...common}>
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
      </svg>
    );
  }
  if (value === "dark") {
    return (
      <svg {...common}>
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
      </svg>
    );
  }
  return (
    <svg {...common}>
      <rect x="2" y="3" width="20" height="14" rx="2" />
      <path d="M8 21h8M12 17v4" />
    </svg>
  );
}

export function ThemeToggle() {
  const { choice, setThemeChoice } = useTheme();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuId = useId();
  const menuRef = useDismiss<HTMLDivElement>(menuOpen, () =>
    setMenuOpen(false),
  );

  return (
    <div ref={menuRef} className="relative flex">
      <button
        type="button"
        aria-label="Theme"
        aria-haspopup="menu"
        aria-expanded={menuOpen}
        aria-controls={menuId}
        onClick={() => setMenuOpen((open) => !open)}
        className="flex h-8 w-8 items-center justify-center rounded border border-border-strong bg-surface text-fg-secondary hover:bg-surface-strong"
      >
        <ThemeIcon value={choice} />
      </button>
      {menuOpen && (
        <div
          id={menuId}
          role="menu"
          aria-label="Theme"
          className="absolute right-0 top-full z-10 mt-2 flex min-w-32 flex-col rounded border border-border bg-surface py-1 shadow-lg"
        >
          {OPTIONS.map(({ value, label }) => (
            <button
              key={value}
              type="button"
              role="menuitemradio"
              aria-checked={choice === value}
              onClick={() => {
                setThemeChoice(value);
                setMenuOpen(false);
              }}
              className="flex items-center gap-2 px-3 py-2 text-left font-medium hover:bg-surface-strong"
            >
              <ThemeIcon value={value} />
              <span className="flex-1">{label}</span>
              {choice === value && (
                <span aria-hidden="true" className="text-primary">
                  ✓
                </span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
