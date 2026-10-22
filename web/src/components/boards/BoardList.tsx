import { Link } from "@tanstack/react-router";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import type { Board } from "../../lib/boards";
import { BOARD_LIMIT, fetchBoards } from "../../lib/boards";
import { useProjectOptions } from "../../lib/projects";

import { ErrorBanner } from "../shared/ErrorBanner";
import { Loading } from "../shared/Loading";
import { Pagination } from "../shared/Pagination";

type BoardListProps = {
  projectId?: string;
  filter?: string;
};

export function BoardList({ projectId, filter }: BoardListProps) {
  const [offset, setOffset] = useState(0);

  const { data, isLoading, error } = useQuery({
    queryKey: ["boards", offset, projectId, filter],
    queryFn: () => fetchBoards(BOARD_LIMIT, offset, { projectId, filter }),
  });

  const { data: projects } = useProjectOptions();

  const projectNames = new Map(
    (projects?.results ?? []).map((p) => [p.id, p.name]),
  );

  const items: Board[] = data?.results ?? [];
  const total = data?.total ?? 0;

  return (
    <div className="space-y-4">
      {error && (
        <ErrorBanner>
          {filter ? `Invalid filter: ${error.message}` : "Error loading boards"}
        </ErrorBanner>
      )}

      {isLoading ? (
        <Loading />
      ) : items.length === 0 ? (
        <div className="text-center text-fg-muted">
          {filter ? "No boards match this filter" : "No boards yet"}
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {items.map((board) => (
            <Link
              key={board.id}
              to="/projects/$id/boards/$boardId"
              params={{ id: board.project_id, boardId: board.id }}
              className="flex flex-col gap-3 rounded border border-border p-4 hover:border-primary hover:bg-primary-subtle transition"
            >
              <div className="min-w-0 flex-1 break-words">
                <h3 className="font-semibold text-primary">{board.name}</h3>
                {board.description && (
                  <p className="mt-1 text-sm text-fg-secondary">
                    {board.description}
                  </p>
                )}
                <p className="mt-1 text-xs text-fg-muted">
                  {projectNames.get(board.project_id) ?? "Unknown"}
                </p>
              </div>
            </Link>
          ))}
        </div>
      )}

      <Pagination
        offset={offset}
        limit={BOARD_LIMIT}
        total={total}
        disabled={isLoading}
        onChange={setOffset}
      />
    </div>
  );
}
