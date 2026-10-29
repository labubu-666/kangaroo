import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useProjectOptions } from "../../lib/projects";
import { bulkDeleteWorkItems } from "../../lib/work-items";

import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { ErrorBanner } from "../../components/shared/ErrorBanner";
import { FilterBubbles } from "../../components/shared/FilterBubbles";
import { WorkItemList } from "../../components/work-items/WorkItemList";
import { ADMIN_WORK_ITEM_FIELDS } from "../../lib/filter-bubbles";

export const Route = createFileRoute("/admin/work-items")({
  component: AdminWorkItems,
  validateSearch: (search: Record<string, unknown>): { filter?: string } => ({
    filter: typeof search.filter === "string" ? search.filter : undefined,
  }),
});

function AdminWorkItems() {
  const { filter } = Route.useSearch();
  useBreadcrumbs([{ label: "Admin", to: "/admin" }, { label: "Work items" }]);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: projects } = useProjectOptions();
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [matchingTotal, setMatchingTotal] = useState(0);

  const setFilter = (next: string | undefined) => {
    setSelected(new Set());
    navigate({ to: "/admin/work-items", search: { filter: next } });
  };

  const deleteMutation = useMutation({
    mutationFn: bulkDeleteWorkItems,
    onSuccess: () => {
      setSelected(new Set());
      queryClient.invalidateQueries({ queryKey: ["work-items"] });
    },
  });

  const deleteSelected = () => {
    const count = selected.size;
    if (
      !confirm(
        `Delete ${count} selected work item(s)? Their child items are deleted too. This cannot be undone.`,
      )
    )
      return;
    deleteMutation.mutate({ ids: [...selected] });
  };

  const deleteAllMatching = () => {
    if (
      !confirm(
        `Delete all ${matchingTotal} work item(s) matching this filter? Their child items are deleted too. This cannot be undone.`,
      )
    )
      return;
    deleteMutation.mutate({ all_matching: true, filter });
  };

  return (
    <div className="space-y-4 p-4">
      <h1 className="text-2xl font-bold">Work items</h1>

      <FilterBubbles
        filter={filter}
        onChange={setFilter}
        projects={projects?.results ?? []}
        fields={ADMIN_WORK_ITEM_FIELDS}
      />

      <div className="flex flex-wrap items-center gap-3">
        <button
          onClick={deleteSelected}
          disabled={selected.size === 0 || deleteMutation.isPending}
          className="rounded bg-danger px-4 py-2 font-medium text-on-primary hover:bg-danger-hover disabled:bg-fg-disabled"
        >
          Delete selected ({selected.size})
        </button>
        <button
          onClick={deleteAllMatching}
          disabled={matchingTotal === 0 || deleteMutation.isPending}
          className="rounded border border-danger px-4 py-2 font-medium text-danger hover:bg-danger-subtle disabled:border-fg-disabled disabled:text-fg-disabled"
        >
          Delete all matching ({matchingTotal})
        </button>
      </div>

      {deleteMutation.error && (
        <ErrorBanner>{deleteMutation.error.message}</ErrorBanner>
      )}

      <WorkItemList
        key={filter ?? ""}
        filter={filter}
        trashed="all"
        selection={{ selected, onChange: setSelected }}
        onTotalChange={setMatchingTotal}
      />
    </div>
  );
}
