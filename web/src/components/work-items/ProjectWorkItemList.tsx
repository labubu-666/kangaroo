import { Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { WORK_ITEM_FIELDS } from "../../lib/filter-bubbles";
import {
  WORK_ITEM_LIMIT,
  WORK_ITEM_SORTS,
  fetchWorkItems,
} from "../../lib/work-items";

import { FilterBubbles } from "../shared/FilterBubbles";
import { CopyId } from "../shared/CopyId";
import { ErrorBanner } from "../shared/ErrorBanner";
import { Loading } from "../shared/Loading";
import { Pagination } from "../shared/Pagination";
import { StatusBadge } from "../shared/StatusBadge";
import { TypeIcon } from "../shared/TypeIcon";

// The project is already fixed, so its fields are left out of the filter
const PROJECT_FIELDS_EXCLUDED = WORK_ITEM_FIELDS.filter(
  (field) => !field.startsWith("project."),
);

// The work items of one project, with its filter, sort and page kept by the parent
export function ProjectWorkItemList({
  projectId,
  filter,
  sort,
  offset,
  onFilterChange,
  onSortChange,
  onOffsetChange,
}: {
  projectId: string;
  filter?: string;
  sort: string;
  offset: number;
  onFilterChange: (filter: string | undefined) => void;
  onSortChange: (sort: string) => void;
  onOffsetChange: (offset: number) => void;
}) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["work-items", offset, projectId, filter, sort],
    queryFn: () =>
      fetchWorkItems(WORK_ITEM_LIMIT, offset, { projectId, filter, sort }),
  });

  const items = data?.results ?? [];
  const total = data?.total ?? 0;

  return (
    <div className="space-y-4">
      <div className="flex items-start gap-4">
        <div className="min-w-0 flex-1">
          <FilterBubbles
            filter={filter}
            onChange={onFilterChange}
            projects={[]}
            fields={PROJECT_FIELDS_EXCLUDED}
          />
        </div>
        <select
          aria-label="Sort work items"
          value={sort}
          onChange={(e) => onSortChange(e.target.value)}
          className="shrink-0 rounded border border-border-strong px-3 py-2"
        >
          {WORK_ITEM_SORTS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {error && <ErrorBanner>Error loading work items</ErrorBanner>}

      {isLoading ? (
        <Loading />
      ) : items.length === 0 ? (
        <div className="text-center text-fg-muted">No work items yet</div>
      ) : (
        <div className="flex flex-col gap-4">
          {items.map((item) => (
            <Link
              key={item.id}
              to="/work-items/$id"
              params={{ id: item.id }}
              className="flex min-w-0 flex-col gap-3 rounded border border-border p-3 hover:border-primary hover:bg-primary-subtle transition"
            >
              <div className="flex items-center gap-2">
                <TypeIcon type={item.type} />
                <h3 className="min-w-0 flex-1 truncate font-semibold text-primary">
                  {item.summary}
                </h3>
                {item.trashed && (
                  <span className="shrink-0 rounded bg-surface-emphasis px-2 py-0.5 text-xs font-medium text-fg-secondary">
                    Trashed
                  </span>
                )}
                <div className="shrink-0">
                  <StatusBadge status={item.status} />
                </div>
              </div>
              {item.labels.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {item.labels.map((label) => (
                    <span
                      key={label}
                      className="rounded bg-surface-strong px-2 py-0.5 text-xs font-medium text-fg-secondary"
                    >
                      {label}
                    </span>
                  ))}
                </div>
              )}
              <div className="flex items-center">
                <CopyId
                  id={item.id}
                  url={`${window.location.origin}/web/work-items/${item.id}`}
                />
              </div>
            </Link>
          ))}
        </div>
      )}

      <Pagination
        offset={offset}
        limit={WORK_ITEM_LIMIT}
        total={total}
        disabled={isLoading}
        onChange={onOffsetChange}
      />
    </div>
  );
}
