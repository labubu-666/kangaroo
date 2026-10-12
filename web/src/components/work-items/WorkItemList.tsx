import { Link } from "@tanstack/react-router";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import type { WorkItem } from "../../lib/work-items";
import { WORK_ITEM_LIMIT, fetchWorkItems } from "../../lib/work-items";

import { CopyId } from "../shared/CopyId";
import { ErrorBanner } from "../shared/ErrorBanner";
import { Loading } from "../shared/Loading";
import { Pagination } from "../shared/Pagination";
import { StatusBadge } from "../shared/StatusBadge";
import { TypeIcon } from "../shared/TypeIcon";

type WorkItemListProps = {
  projectId?: string;
  filter?: string;
  trashed?: boolean | "all";
};

export function WorkItemList({
  projectId,
  filter,
  trashed,
}: WorkItemListProps) {
  const [offset, setOffset] = useState(0);

  const { data, isLoading, error } = useQuery({
    queryKey: ["work-items", offset, projectId, filter, trashed],
    queryFn: () =>
      fetchWorkItems(WORK_ITEM_LIMIT, offset, {
        projectId,
        filter,
        trashed,
      }),
  });

  const items: WorkItem[] = data?.results ?? [];
  const total = data?.total ?? 0;

  return (
    <div className="space-y-4">
      {error && <ErrorBanner>Error loading work items</ErrorBanner>}

      {isLoading ? (
        <Loading />
      ) : items.length === 0 ? (
        <div className="text-center text-gray-500">No work items yet</div>
      ) : (
        <div className="flex flex-col gap-4">
          {items.map((item) => (
            <Link
              key={item.id}
              to="/work-items/$id"
              params={{ id: item.id }}
              className="flex flex-col gap-3 rounded border border-gray-200 p-3 hover:border-blue-400 hover:bg-blue-50 transition"
            >
              <div className="flex items-center gap-2">
                <TypeIcon type={item.type} />
                <h3 className="min-w-0 flex-1 truncate font-semibold text-blue-600">
                  {item.title}
                </h3>
                {item.trashed && (
                  <span className="shrink-0 rounded bg-gray-200 px-2 py-0.5 text-xs font-medium text-gray-700">
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
                      className="rounded bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-700"
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
        onChange={setOffset}
      />
    </div>
  );
}
