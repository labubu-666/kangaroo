import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useProjectOptions } from "../../lib/projects";

import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
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

  const { data: projects } = useProjectOptions();

  const setFilter = (next: string | undefined) => {
    navigate({ to: "/admin/work-items", search: { filter: next } });
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

      <WorkItemList key={filter ?? ""} filter={filter} trashed="all" />
    </div>
  );
}
