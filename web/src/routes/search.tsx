import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { fetchProject } from "../lib/projects";
import { searchAll } from "../lib/search";

import { ErrorBanner } from "../components/shared/ErrorBanner";
import { Loading } from "../components/shared/Loading";
import { StatusBadge } from "../components/shared/StatusBadge";
import { TypeBadge } from "../components/shared/TypeBadge";

const RESULTS_LIMIT = 20;

// Shows the project a board belongs to, since boards live under projects
function BoardProjectName({ projectId }: { projectId: string }) {
  const { data: project } = useQuery({
    queryKey: ["projects", projectId],
    queryFn: () => fetchProject(projectId),
  });
  return project ? (
    <p className="text-sm text-gray-600">Project: {project.name}</p>
  ) : null;
}

export const Route = createFileRoute("/search")({
  component: SearchResults,
  validateSearch: (search: Record<string, unknown>): { q: string } => ({
    q: typeof search.q === "string" ? search.q : "",
  }),
});

function SearchResults() {
  const { q } = Route.useSearch();
  const term = q.trim();

  const { data, isLoading, error } = useQuery({
    queryKey: ["search", "results", term],
    queryFn: () => searchAll(term, RESULTS_LIMIT),
    enabled: term !== "",
  });

  return (
    <div className="space-y-6 p-4">
      <h1 className="text-2xl font-bold">
        {term ? `Results for "${term}"` : "Search"}
      </h1>

      {!term ? (
        <div className="text-center text-gray-500">
          Type something in the search bar to find work items, projects and
          boards.
        </div>
      ) : error ? (
        <ErrorBanner>Error loading search results</ErrorBanner>
      ) : isLoading || !data ? (
        <Loading />
      ) : (
        <>
          <section className="space-y-3">
            <h2 className="text-lg font-semibold">
              Work items ({data.workItems.total})
            </h2>
            {data.workItems.results.length === 0 ? (
              <p className="text-sm text-gray-500">No matching work items</p>
            ) : (
              data.workItems.results.map((item) => (
                <Link
                  key={item.id}
                  to="/work-items/$id"
                  params={{ id: item.id }}
                  className="flex flex-col gap-2 rounded border border-gray-200 p-4 hover:border-blue-400 hover:bg-blue-50 transition sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-semibold text-blue-600">
                      {item.title}
                    </h3>
                    <TypeBadge type={item.type} />
                  </div>
                  <StatusBadge status={item.status} />
                </Link>
              ))
            )}
          </section>

          <section className="space-y-3">
            <h2 className="text-lg font-semibold">
              Projects ({data.projects.total})
            </h2>
            {data.projects.results.length === 0 ? (
              <p className="text-sm text-gray-500">No matching projects</p>
            ) : (
              data.projects.results.map((project) => (
                <Link
                  key={project.id}
                  to="/projects/$id"
                  params={{ id: project.id }}
                  className="flex flex-col gap-1 rounded border border-gray-200 p-4 hover:border-blue-400 hover:bg-blue-50 transition"
                >
                  <h3 className="font-semibold text-blue-600">
                    {project.name}
                  </h3>
                  {project.description && (
                    <p className="text-sm text-gray-600">
                      {project.description}
                    </p>
                  )}
                </Link>
              ))
            )}
          </section>

          <section className="space-y-3">
            <h2 className="text-lg font-semibold">
              Boards ({data.boards.total})
            </h2>
            {data.boards.results.length === 0 ? (
              <p className="text-sm text-gray-500">No matching boards</p>
            ) : (
              data.boards.results.map((board) => (
                <Link
                  key={board.id}
                  to="/projects/$id/boards/$boardId"
                  params={{ id: board.project_id, boardId: board.id }}
                  className="flex flex-col gap-1 rounded border border-gray-200 p-4 hover:border-blue-400 hover:bg-blue-50 transition"
                >
                  <h3 className="font-semibold text-blue-600">{board.name}</h3>
                  <BoardProjectName projectId={board.project_id} />
                  {board.description && (
                    <p className="text-sm text-gray-600">{board.description}</p>
                  )}
                </Link>
              ))
            )}
          </section>
        </>
      )}
    </div>
  );
}
