import type { ReactNode } from "react";

export function RunButton({
  onClick,
  disabled,
  children,
}: {
  onClick: () => void;
  disabled: boolean;
  children: ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="flex h-10 items-center gap-2 rounded bg-green-600 px-4 font-medium text-on-primary hover:bg-green-700 dark:bg-green-700 dark:hover:bg-green-800 disabled:bg-fg-disabled"
    >
      <svg
        aria-hidden="true"
        viewBox="0 0 24 24"
        className="h-4 w-4 fill-current"
      >
        <path d="M8 5v14l11-7z" />
      </svg>
      {children}
    </button>
  );
}
