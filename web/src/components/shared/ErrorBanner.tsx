import type { ReactNode } from "react";

export function ErrorBanner({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-md border border-red-200 dark:border-red-900 bg-danger-subtle p-3 text-danger-hover">
      {children}
    </div>
  );
}
