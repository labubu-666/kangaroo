import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import type { Project } from "../../lib/projects";
import { PROJECT_LIMIT, fetchProjects } from "../../lib/projects";

import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { ErrorBanner } from "../../components/shared/ErrorBanner";
import { Loading } from "../../components/shared/Loading";
import { Pagination } from "../../components/shared/Pagination";

export const Route = createFileRoute("/projects/")({
  component: ProjectsList,
});

function ProjectsList() {
  const [offset, setOffset] = useState(0);
  useBreadcrumbs([{ label: "Projects" }]);

  const { data, isLoading, error } = useQuery({
    queryKey: ["projects", offset],
    queryFn: () => fetchProjects(PROJECT_LIMIT, offset),
  });

  const items: Project[] = data?.results ?? [];
  const total = data?.total ?? 0;

  return (
    <div className="space-y-4 p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
        <h1 className="text-2xl font-bold">Projects</h1>
        <Link
          to="/projects/create"
          className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
        >
          New project
        </Link>
      </div>

      {error && <ErrorBanner>Error loading projects</ErrorBanner>}

      {isLoading ? (
        <Loading />
      ) : items.length === 0 ? (
        <div className="text-center text-gray-500">No projects yet</div>
      ) : (
        <div className="flex flex-col gap-4">
          {items.map((project) => (
            <Link
              key={project.id}
              to="/projects/$id"
              params={{ id: project.id }}
              className="flex flex-col gap-3 rounded border border-gray-200 p-4 hover:border-blue-400 hover:bg-blue-50 transition"
            >
              <div className="min-w-0 flex-1 break-words">
                <h3 className="font-semibold text-blue-600">{project.name}</h3>
                {project.description && (
                  <p className="mt-1 text-sm text-gray-600">
                    {project.description}
                  </p>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}

      <Pagination
        offset={offset}
        limit={PROJECT_LIMIT}
        total={total}
        disabled={isLoading}
        onChange={setOffset}
      />
    </div>
  );
}
