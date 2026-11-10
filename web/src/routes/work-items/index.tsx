import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useProjectOptions } from "../../lib/projects";

import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { FilterBubbles } from "../../components/shared/FilterBubbles";
import { StatusPicker } from "../../components/work-items/StatusPicker";
import { WorkItemList } from "../../components/work-items/WorkItemList";
import {
  WORK_ITEM_FIELDS,
  projectIdFromFilter,
  statusIdFromFilter,
  withStatus,
} from "../../lib/filter-bubbles";
import { WORK_ITEM_DEFAULT_SORT, WORK_ITEM_SORTS } from "../../lib/work-items";

export const Route = createFileRoute("/work-items/")({
  component: WorkItemsList,
  validateSearch: (
    search: Record<string, unknown>,
  ): { filter?: string; sort?: string } => ({
    filter: typeof search.filter === "string" ? search.filter : undefined,
    sort: WORK_ITEM_SORTS.find((option) => option.value === search.sort)?.value,
  }),
});

function WorkItemsList() {
  const { filter, sort = WORK_ITEM_DEFAULT_SORT } = Route.useSearch();
  useBreadcrumbs([{ label: "Work items" }]);
  const navigate = useNavigate();

  const { data: projects } = useProjectOptions();

  const setFilter = (next: string | undefined) => {
    navigate({ to: "/work-items", search: { filter: next, sort } });
  };

  // "New work item" pre-selects the project when the filter shows just one
  const projectId = filter ? projectIdFromFilter(filter) : undefined;
  const statusId = filter ? statusIdFromFilter(filter) : undefined;

  return (
    <div className="space-y-4 p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
        <h1 className="text-2xl font-bold">Work items</h1>
        <Link
          to="/work-items/create"
          search={{ projectId }}
          className="rounded bg-primary px-4 py-2 font-medium text-on-primary hover:bg-primary-hover"
        >
          New work item
        </Link>
      </div>

      {projectId && (
        <StatusPicker
          projectId={projectId}
          statusId={statusId}
          onChange={(next) => setFilter(withStatus(filter, next))}
        />
      )}

      <div className="flex items-start gap-4">
        <div className="min-w-0 flex-1">
          <FilterBubbles
            filter={filter}
            onChange={setFilter}
            projects={projects?.results ?? []}
            fields={WORK_ITEM_FIELDS}
          />
        </div>
        <select
          aria-label="Sort work items"
          value={sort}
          onChange={(e) => {
            navigate({
              to: "/work-items",
              search: { filter, sort: e.target.value },
            });
          }}
          className="shrink-0 rounded border border-border-strong px-3 py-2"
        >
          {WORK_ITEM_SORTS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <WorkItemList
        key={`${filter ?? ""}|${sort}`}
        filter={filter}
        sort={sort}
      />
    </div>
  );
}
