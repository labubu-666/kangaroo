import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";

import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { ErrorBanner } from "../../components/shared/ErrorBanner";
import { BACKUP_URL, restoreBackup } from "../../lib/backup";
import { fetchSettings } from "../../lib/settings";

type AdminTab = "backup" | "manage-work-items" | "settings";

export const Route = createFileRoute("/admin/")({
  component: Admin,
  validateSearch: (search: Record<string, unknown>): { tab?: AdminTab } => ({
    tab:
      search.tab === "manage-work-items" || search.tab === "settings"
        ? search.tab
        : "backup",
  }),
});

const TABS: { value: AdminTab; label: string }[] = [
  { value: "backup", label: "Backup and restore" },
  { value: "manage-work-items", label: "Manage work items" },
  { value: "settings", label: "Settings" },
];

function SettingsTab() {
  const { data, error, isLoading } = useQuery({
    queryKey: ["settings"],
    queryFn: fetchSettings,
  });

  if (isLoading) return <p>Loading settings...</p>;
  if (error) return <ErrorBanner>{error.message}</ErrorBanner>;
  return (
    <pre className="overflow-x-auto rounded border border-border bg-surface p-4 text-sm text-fg">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}

function Admin() {
  useBreadcrumbs([{ label: "Admin" }]);
  const { tab = "backup" } = Route.useSearch();
  const queryClient = useQueryClient();
  const fileInput = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);

  const restoreMutation = useMutation({
    mutationFn: restoreBackup,
    onSuccess: () => {
      setFile(null);
      if (fileInput.current) fileInput.current.value = "";
      // The restore replaces every table, so refresh all cached data.
      queryClient.invalidateQueries();
    },
  });

  const restore = () => {
    if (!file) return;
    if (
      !confirm(
        "Restore this backup? All current data will be replaced. This cannot be undone.",
      )
    )
      return;
    restoreMutation.mutate(file);
  };

  return (
    <div className="space-y-4 p-4 sm:p-8">
      <h1 className="text-2xl font-bold">Admin</h1>

      <div role="tablist" className="flex gap-4 border-b border-border">
        {TABS.map((t) => (
          <Link
            key={t.value}
            role="tab"
            aria-selected={tab === t.value}
            to="/admin"
            search={{ tab: t.value }}
            replace
            className={`-mb-px border-b-2 px-1 pb-2 font-semibold ${
              tab === t.value
                ? "border-primary text-primary"
                : "border-transparent text-fg-muted hover:text-fg"
            }`}
          >
            {t.label}
          </Link>
        ))}
      </div>

      {tab === "manage-work-items" ? (
        <ul className="list-disc space-y-2 pl-5">
          <li>
            <Link
              to="/admin/work-items"
              className="text-primary hover:underline"
            >
              All work items
            </Link>
          </li>
          <li>
            <Link
              to="/admin/work-items"
              search={{ filter: "trashed == true" }}
              className="text-primary hover:underline"
            >
              Trashed work items
            </Link>
          </li>
        </ul>
      ) : tab === "settings" ? (
        <SettingsTab />
      ) : (
        <section className="space-y-2">
          <p>
            <a
              href={BACKUP_URL}
              download
              className="text-primary hover:underline"
            >
              Download backup
            </a>
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <input
              ref={fileInput}
              type="file"
              accept=".zip,application/zip"
              aria-label="Backup file"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              disabled={restoreMutation.isPending}
            />
            <button
              onClick={restore}
              disabled={!file || restoreMutation.isPending}
              className="rounded bg-danger px-4 py-2 font-medium text-on-primary hover:bg-danger-hover disabled:bg-fg-disabled"
            >
              {restoreMutation.isPending ? "Restoring..." : "Restore from file"}
            </button>
          </div>
          {restoreMutation.isSuccess && (
            <p className="text-green-700 dark:text-green-400">
              Backup restored.
            </p>
          )}
          {restoreMutation.isError && (
            <ErrorBanner>{restoreMutation.error.message}</ErrorBanner>
          )}
        </section>
      )}
    </div>
  );
}
