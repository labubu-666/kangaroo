import type { ReactNode } from "react";

export function ErrorBanner({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-md border border-red-200 bg-red-50 p-3 text-red-700">
      {children}
    </div>
  );
}
