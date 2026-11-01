import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { fetchProject } from "../lib/projects";
import { searchAll } from "../lib/search";

import { ErrorBanner } from "../components/shared/ErrorBanner";
import { Highlight } from "../components/shared/Highlight";
import { SearchSnippet } from "../components/shared/SearchSnippet";
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
    <p className="text-sm text-fg-secondary">Project: {project.name}</p>
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
        <div className="text-center text-fg-muted">
          Type something in the search bar to find work items, projects, boards,
          knowledge bases and articles.
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
              <p className="text-sm text-fg-muted">No matching work items</p>
            ) : (
              data.workItems.results.map((item) => (
                <Link
                  key={item.id}
                  to="/work-items/$id"
                  params={{ id: item.id }}
                  className="flex flex-col gap-2 rounded border border-border p-4 hover:border-primary hover:bg-primary-subtle transition sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="flex flex-col gap-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-semibold text-primary">
                        <Highlight text={item.summary} term={term} />
                      </h3>
                      <TypeBadge type={item.type} />
                    </div>
                    <SearchSnippet hit={item.snippet ?? null} term={term} />
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
              <p className="text-sm text-fg-muted">No matching projects</p>
            ) : (
              data.projects.results.map((project) => (
                <Link
                  key={project.id}
                  to="/projects/$id"
                  params={{ id: project.id }}
                  className="flex flex-col gap-1 rounded border border-border p-4 hover:border-primary hover:bg-primary-subtle transition"
                >
                  <h3 className="font-semibold text-primary">
                    <Highlight text={project.name} term={term} />
                  </h3>
                  {project.description && (
                    <p className="text-sm text-fg-secondary">
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
              <p className="text-sm text-fg-muted">No matching boards</p>
            ) : (
              data.boards.results.map((board) => (
                <Link
                  key={board.id}
                  to="/projects/$id/boards/$boardId"
                  params={{ id: board.project_id, boardId: board.id }}
                  className="flex flex-col gap-1 rounded border border-border p-4 hover:border-primary hover:bg-primary-subtle transition"
                >
                  <h3 className="font-semibold text-primary">
                    <Highlight text={board.name} term={term} />
                  </h3>
                  <BoardProjectName projectId={board.project_id} />
                  {board.description && (
                    <p className="text-sm text-fg-secondary">
                      {board.description}
                    </p>
                  )}
                </Link>
              ))
            )}
          </section>

          <section className="space-y-3">
            <h2 className="text-lg font-semibold">
              Knowledge bases ({data.knowledgeBases.total})
            </h2>
            {data.knowledgeBases.results.length === 0 ? (
              <p className="text-sm text-fg-muted">
                No matching knowledge bases
              </p>
            ) : (
              data.knowledgeBases.results.map((knowledgeBase) => (
                <Link
                  key={knowledgeBase.id}
                  to="/knowledge-bases/$id"
                  params={{ id: knowledgeBase.id }}
                  className="flex flex-col gap-1 rounded border border-border p-4 hover:border-primary hover:bg-primary-subtle transition"
                >
                  <h3 className="font-semibold text-primary">
                    {knowledgeBase.name}
                  </h3>
                  {knowledgeBase.description && (
                    <p className="text-sm text-fg-secondary">
                      {knowledgeBase.description}
                    </p>
                  )}
                </Link>
              ))
            )}
          </section>

          <section className="space-y-3">
            <h2 className="text-lg font-semibold">
              Articles ({data.articles.total})
            </h2>
            {data.articles.results.length === 0 ? (
              <p className="text-sm text-fg-muted">No matching articles</p>
            ) : (
              data.articles.results.map((article) => (
                <Link
                  key={article.id}
                  to="/articles/$id"
                  params={{ id: article.id }}
                  className="flex flex-col gap-1 rounded border border-border p-4 hover:border-primary hover:bg-primary-subtle transition"
                >
                  <h3 className="font-semibold text-primary">
                    <Highlight text={article.title} term={term} />
                  </h3>
                  <SearchSnippet hit={article.snippet ?? null} term={term} />
                </Link>
              ))
            )}
          </section>
        </>
      )}
    </div>
  );
}
