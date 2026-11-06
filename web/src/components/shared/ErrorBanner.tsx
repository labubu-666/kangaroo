import type { ReactNode } from "react";

export function ErrorBanner({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-md border border-danger/30 bg-danger-subtle p-3 text-danger-hover">
      {children}
    </div>
  );
}
