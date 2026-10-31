import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useProjectOptions } from "../../lib/projects";

import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { BoardList } from "../../components/boards/BoardList";
import { FilterBubbles } from "../../components/shared/FilterBubbles";
import { FilterPreview } from "../../components/boards/FilterPreview";
import { projectIdFromFilter } from "../../lib/filter-bubbles";

export const Route = createFileRoute("/boards/")({
  component: BoardsList,
  validateSearch: (search: Record<string, unknown>): { filter?: string } => ({
    filter: typeof search.filter === "string" ? search.filter : undefined,
  }),
});

function BoardsList() {
  const { filter } = Route.useSearch();
  const navigate = useNavigate();

  const setFilter = (next: string | undefined) => {
    navigate({ to: "/boards", search: { filter: next } });
  };

  const { data: projects } = useProjectOptions();

  const projectId = filter ? projectIdFromFilter(filter) : undefined;
  const project = projects?.results.find((p) => p.id === projectId);
  useBreadcrumbs(
    projectId
      ? [
          { label: "Projects", to: "/projects" },
          {
            label: project?.name ?? "Loading...",
            to: "/projects/$id",
            params: { id: projectId },
          },
          { label: "Boards" },
        ]
      : [{ label: "Boards" }],
  );

  return (
    <div className="space-y-4 p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
        <h1 className="text-2xl font-bold">Boards</h1>
      </div>

      <FilterBubbles
        filter={filter}
        onChange={setFilter}
        projects={projects?.results ?? []}
      />

      {filter && <FilterPreview filter={filter} />}

      <BoardList key={filter ?? ""} filter={filter} />
    </div>
  );
}
