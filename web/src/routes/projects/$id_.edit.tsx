import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { deleteProject, fetchProject, updateProject } from "../../lib/projects";
import { removeRecent } from "../../lib/recent";
import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";

import { ErrorBanner } from "../../components/shared/ErrorBanner";
import { Loading } from "../../components/shared/Loading";

export const Route = createFileRoute("/projects/$id_/edit")({
  component: EditProject,
});

interface ProjectForm {
  name: string;
  description: string;
}

function EditProject() {
  const { id } = Route.useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const {
    data: project,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["projects", id],
    queryFn: () => fetchProject(id),
  });

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    setError,
  } = useForm<ProjectForm>({
    values: project
      ? { name: project.name, description: project.description ?? "" }
      : undefined,
  });

  const mutation = useMutation({
    mutationFn: (data: ProjectForm) =>
      updateProject(id, {
        name: data.name.trim(),
        description: data.description.trim() || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      navigate({ to: "/projects/$id", params: { id } });
    },
    onError: (err) => {
      setError("root", {
        message: err.message,
      });
    },
  });

  const deleteProjectMutation = useMutation({
    mutationFn: () => deleteProject(id),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: ["projects", id] });
      removeRecent("project", id);
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      navigate({ to: "/projects" });
    },
  });

  const handleDeleteProject = () => {
    if (confirm("Are you sure you want to delete this project?")) {
      deleteProjectMutation.mutate();
    }
  };

  const onSubmit = (data: ProjectForm) => {
    if (!data.name.trim()) {
      setError("name", { message: "Name is required" });
      return;
    }
    mutation.mutate(data);
  };

  useBreadcrumbs([
    { label: "Projects", to: "/projects" },
    {
      label: project?.name ?? "Loading...",
      to: "/projects/$id",
      params: { id },
    },
    { label: "Edit" },
  ]);

  return (
    <div className="space-y-6 p-4">
      {error && <ErrorBanner>Error loading project</ErrorBanner>}

      {isLoading ? (
        <Loading />
      ) : project ? (
        <form
          onSubmit={handleSubmit(onSubmit)}
          autoComplete="off"
          className="space-y-4 rounded border border-border p-4"
        >
          {errors.root && <ErrorBanner>{errors.root.message}</ErrorBanner>}

          <div className="space-y-2">
            <label htmlFor="name" className="block font-medium">
              Name *
            </label>
            <input
              id="name"
              type="text"
              disabled={mutation.isPending}
              placeholder="Enter project name"
              className="w-full rounded border border-border-strong px-3 py-2"
              {...register("name", { required: "Name is required" })}
            />
            {errors.name && (
              <p className="text-sm text-danger">{errors.name.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <label htmlFor="description" className="block font-medium">
              Description
            </label>
            <textarea
              id="description"
              disabled={mutation.isPending}
              placeholder="Enter project description (optional)"
              rows={4}
              className="w-full rounded border border-border-strong px-3 py-2"
              {...register("description")}
            />
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              type="submit"
              disabled={mutation.isPending || !isDirty}
              className="rounded bg-primary px-4 py-2 font-medium text-on-primary hover:bg-primary-hover disabled:bg-fg-disabled"
            >
              {mutation.isPending ? "Saving..." : "Save"}
            </button>
            <Link
              to="/projects/$id"
              params={{ id }}
              className="rounded border border-border-strong px-4 py-2 font-medium hover:bg-surface-muted"
            >
              Cancel
            </Link>
          </div>
        </form>
      ) : null}

      {project && (
        <div className="border-t border-border pt-4">
          {deleteProjectMutation.error && (
            <ErrorBanner>{deleteProjectMutation.error.message}</ErrorBanner>
          )}
          <button
            onClick={handleDeleteProject}
            disabled={deleteProjectMutation.isPending}
            className="rounded bg-danger px-4 py-2 font-medium text-on-primary hover:bg-danger-hover disabled:bg-fg-disabled"
          >
            Delete project
          </button>
        </div>
      )}
    </div>
  );
}
