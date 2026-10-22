import { useEffect, useState, type ReactNode } from "react";

export function CopyBase({
  value,
  ariaLabel,
  title = "Copy link",
  children,
}: {
  value: string;
  ariaLabel: string;
  title?: string;
  children?: ReactNode;
}) {
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!copied) return;
    const timer = setTimeout(() => setCopied(false), 1500);
    return () => clearTimeout(timer);
  }, [copied]);

  const handleClick = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    e.stopPropagation();
    await navigator.clipboard.writeText(value);
    setCopied(true);
  };

  return (
    <button
      type="button"
      title={title}
      aria-label={ariaLabel}
      onClick={handleClick}
      onPointerDown={(e) => e.stopPropagation()}
      style={{ display: "inline-flex" }}
      className="max-w-full cursor-pointer items-center gap-1 whitespace-nowrap rounded bg-surface-strong px-1.5 py-0.5 font-mono text-xs text-fg-secondary hover:bg-surface-emphasis"
    >
      {children}
      {copied ? (
        <span className="shrink-0 font-sans font-medium text-fg-secondary">
          Copied!
        </span>
      ) : (
        <svg
          aria-hidden="true"
          width={12}
          height={12}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          className="flex-none"
        >
          <rect x="9" y="9" width="13" height="13" rx="2" />
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
        </svg>
      )}
    </button>
  );
}
