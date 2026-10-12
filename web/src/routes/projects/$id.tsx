import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchProject, updateProject } from "../../lib/projects";
import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";

import { BoardList } from "../../components/boards/BoardList";
import { ErrorBanner } from "../../components/shared/ErrorBanner";
import { InlineEdit } from "../../components/InlineEdit";
import { Loading } from "../../components/shared/Loading";
import { WorkItemList } from "../../components/work-items/WorkItemList";

type ProjectTab = "boards" | "work-items";

export const Route = createFileRoute("/projects/$id")({
  component: ProjectDetail,
  validateSearch: (search: Record<string, unknown>): { tab?: ProjectTab } => ({
    tab: search.tab === "boards" ? "boards" : "work-items",
  }),
});

const TABS: { value: ProjectTab; label: string }[] = [
  { value: "work-items", label: "Work items" },
  { value: "boards", label: "Boards" },
];

function ProjectDetail() {
  const { id } = Route.useParams();
  const { tab = "work-items" } = Route.useSearch();
  const queryClient = useQueryClient();

  const {
    data: project,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["projects", id],
    queryFn: () => fetchProject(id),
  });

  const saveName = async (name: string) => {
    await updateProject(id, { name: name.trim() });
    queryClient.invalidateQueries({ queryKey: ["projects"] });
  };

  useBreadcrumbs([
    { label: "Projects", to: "/projects" },
    { label: project?.name ?? "Loading..." },
  ]);

  return (
    <div className="space-y-6 p-4">
      {error && <ErrorBanner>Error loading project</ErrorBanner>}

      {isLoading ? (
        <Loading />
      ) : project ? (
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              <InlineEdit
                value={project.name}
                onSave={saveName}
                ariaLabel="name"
                placeholder="Enter project name"
                requiredMessage="Name is required"
                textClassName="text-2xl font-bold sm:text-3xl"
              >
                <h1 className="cursor-pointer break-words text-2xl font-bold sm:text-3xl">
                  {project.name}
                </h1>
              </InlineEdit>
            </div>
            <div className="flex flex-wrap gap-3">
              <Link
                to="/projects/$id/statuses"
                params={{ id: project.id }}
                className="rounded border border-gray-300 px-4 py-2 font-medium hover:bg-gray-50"
              >
                Statuses and types
              </Link>
              <Link
                to="/projects/$id/edit"
                params={{ id: project.id }}
                className="rounded border border-gray-300 px-4 py-2 font-medium hover:bg-gray-50"
              >
                Edit
              </Link>
            </div>
          </div>

          {project.description && (
            <div className="mt-4">
              <h2 className="mb-2 font-semibold text-gray-700">Description</h2>
              <p className="whitespace-pre-wrap text-gray-600">
                {project.description}
              </p>
            </div>
          )}

          <div className="space-y-4">
            <div role="tablist" className="flex gap-4 border-b border-gray-200">
              {TABS.map((t) => (
                <Link
                  key={t.value}
                  role="tab"
                  aria-selected={tab === t.value}
                  to="/projects/$id"
                  params={{ id: project.id }}
                  search={{ tab: t.value }}
                  replace
                  className={`-mb-px border-b-2 px-1 pb-2 font-semibold ${
                    tab === t.value
                      ? "border-blue-600 text-blue-600"
                      : "border-transparent text-gray-500 hover:text-gray-800"
                  }`}
                >
                  {t.label}
                </Link>
              ))}
            </div>

            {tab === "boards" ? (
              <>
                <div className="flex justify-end">
                  <Link
                    to="/projects/$id/boards/create"
                    params={{ id: project.id }}
                    className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
                  >
                    New board
                  </Link>
                </div>
                <BoardList projectId={project.id} />
              </>
            ) : (
              <>
                <div className="flex justify-end">
                  <Link
                    to="/work-items/create"
                    search={{ projectId: project.id }}
                    className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
                  >
                    New work item
                  </Link>
                </div>
                <WorkItemList projectId={project.id} />
              </>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
