import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useId, useState } from "react";
import { fetchProject, updateProject } from "../../lib/projects";
import { useDismiss } from "../../lib/use-dismiss";
import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { useRecordRecent } from "../../lib/recent";

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
  const [menuOpen, setMenuOpen] = useState(false);
  const menuId = useId();
  const menuRef = useDismiss<HTMLDivElement>(menuOpen, () =>
    setMenuOpen(false),
  );

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

  useRecordRecent(
    project && {
      type: "project",
      id: project.id,
      title: project.name,
      to: "/projects/$id",
      params: { id: project.id },
    },
  );

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
            <div ref={menuRef} className="relative">
              <button
                type="button"
                aria-label="More actions"
                aria-haspopup="menu"
                aria-expanded={menuOpen}
                aria-controls={menuId}
                onClick={() => setMenuOpen((open) => !open)}
                className="flex h-10 items-center rounded border border-border-strong px-4 font-medium hover:bg-surface-muted"
              >
                ⋯
              </button>
              {menuOpen && (
                <div
                  id={menuId}
                  role="menu"
                  aria-label="Project actions"
                  className="absolute right-0 z-10 mt-2 flex min-w-40 flex-col rounded border border-border bg-surface py-1 shadow-lg"
                >
                  <Link
                    to="/projects/$id/statuses"
                    params={{ id: project.id }}
                    role="menuitem"
                    onClick={() => setMenuOpen(false)}
                    className="px-3 py-2 font-medium hover:bg-surface-strong"
                  >
                    Statuses and types
                  </Link>
                  <Link
                    to="/projects/$id/edit"
                    params={{ id: project.id }}
                    role="menuitem"
                    onClick={() => setMenuOpen(false)}
                    className="px-3 py-2 font-medium hover:bg-surface-strong"
                  >
                    Edit
                  </Link>
                </div>
              )}
            </div>
          </div>

          {project.description && (
            <div className="mt-4">
              <h2 className="mb-2 font-semibold text-fg-secondary">
                Description
              </h2>
              <p className="whitespace-pre-wrap text-fg-secondary">
                {project.description}
              </p>
            </div>
          )}

          <div className="space-y-4">
            <div role="tablist" className="flex gap-4 border-b border-border">
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
                      ? "border-primary text-primary"
                      : "border-transparent text-fg-muted hover:text-fg"
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
                    className="rounded bg-primary px-4 py-2 font-medium text-on-primary hover:bg-primary-hover"
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
                    className="rounded bg-primary px-4 py-2 font-medium text-on-primary hover:bg-primary-hover"
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
