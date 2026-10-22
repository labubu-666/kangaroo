import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";

import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { ErrorBanner } from "../../components/shared/ErrorBanner";
import { BACKUP_URL, restoreBackup } from "../../lib/backup";

export const Route = createFileRoute("/admin/")({
  component: Admin,
});

function Admin() {
  useBreadcrumbs([{ label: "Admin" }]);
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

      <section className="space-y-2">
        <h2 className="text-xl font-semibold">Backup and restore</h2>
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
          <p className="text-green-700 dark:text-green-400">Backup restored.</p>
        )}
        {restoreMutation.isError && (
          <ErrorBanner>{restoreMutation.error.message}</ErrorBanner>
        )}
      </section>

      <section className="space-y-2">
        <h2 className="text-xl font-semibold">Work items</h2>
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
      </section>
    </div>
  );
}
