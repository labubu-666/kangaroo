import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { deleteBoard, fetchBoard, updateBoard } from "../../lib/boards";
import { removeRecent } from "../../lib/recent";
import { fetchProject, useProjectOptions } from "../../lib/projects";
import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";

import { ErrorBanner } from "../../components/shared/ErrorBanner";
import { Loading } from "../../components/shared/Loading";

export const Route = createFileRoute("/projects/$id_/boards/$boardId_/edit")({
  component: EditBoard,
});

interface BoardForm {
  name: string;
  description: string;
  projectId: string;
  filter: string;
}

function EditBoard() {
  const { id, boardId } = Route.useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const {
    data: board,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["boards", boardId],
    queryFn: () => fetchBoard(boardId),
  });

  const { data: project } = useQuery({
    queryKey: ["projects", id],
    queryFn: () => fetchProject(id),
  });

  const { data: projects } = useProjectOptions();

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    setError,
  } = useForm<BoardForm>({
    values: board
      ? {
          name: board.name,
          description: board.description ?? "",
          projectId: board.project_id,
          filter: board.filter ?? "",
        }
      : undefined,
  });

  const mutation = useMutation({
    mutationFn: (data: BoardForm) =>
      updateBoard(boardId, {
        name: data.name.trim(),
        description: data.description.trim() || null,
        project_id: data.projectId,
        filter: data.filter.trim() || null,
      }),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ["boards"] });
      navigate({
        to: "/projects/$id/boards/$boardId",
        params: { id: updated.project_id, boardId },
      });
    },
    onError: (err) => {
      setError("root", {
        message: err.message,
      });
    },
  });

  const deleteBoardMutation = useMutation({
    mutationFn: () => deleteBoard(boardId),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: ["boards", boardId] });
      removeRecent("board", boardId);
      queryClient.invalidateQueries({ queryKey: ["boards"] });
      navigate({ to: "/projects/$id", params: { id } });
    },
  });

  const handleDeleteBoard = () => {
    if (confirm("Are you sure you want to delete this board?")) {
      deleteBoardMutation.mutate();
    }
  };

  const onSubmit = (data: BoardForm) => {
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
    {
      label: "Boards",
      to: "/boards",
      search: { filter: `project.id == '${id}'` },
    },
    {
      label: board?.name ?? "Loading...",
      to: "/projects/$id/boards/$boardId",
      params: { id, boardId },
    },
    { label: "Edit" },
  ]);

  return (
    <div className="space-y-6 p-4">
      {error && <ErrorBanner>Error loading board</ErrorBanner>}

      {isLoading ? (
        <Loading />
      ) : board ? (
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
              placeholder="Enter board name"
              className="w-full rounded border border-border-strong px-3 py-2"
              {...register("name", { required: "Name is required" })}
            />
            {errors.name && (
              <p className="text-sm text-danger">{errors.name.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <label htmlFor="filter" className="block font-medium">
              Filter
            </label>
            <input
              id="filter"
              type="text"
              disabled={mutation.isPending}
              placeholder="status != 'done' and type == 'task'"
              className="w-full rounded border border-border-strong px-3 py-2 font-mono"
              {...register("filter")}
            />
            <p className="text-sm text-fg-muted">
              Narrows the project's work items. Text fields: title, description,
              status, type, parent_id, project.id, project.name. List field:
              labels (use contains, in, ~ or is empty). Combine with and, or,
              not and parentheses. Leave empty to show all work items in the
              project. See{" "}
              <Link
                to="/docs/$doc"
                params={{ doc: "filter-language" }}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary underline"
              >
                the filter language docs
              </Link>{" "}
              for details.
            </p>
          </div>

          <div className="space-y-2">
            <label htmlFor="projectId" className="block font-medium">
              Project
            </label>
            <select
              id="projectId"
              disabled={mutation.isPending}
              className="w-full rounded border border-border-strong px-3 py-2"
              {...register("projectId")}
            >
              {(projects?.results ?? []).map((option) => (
                <option key={option.id} value={option.id}>
                  {option.name}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <label htmlFor="description" className="block font-medium">
              Description
            </label>
            <textarea
              id="description"
              disabled={mutation.isPending}
              placeholder="Enter board description (optional)"
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
              to="/projects/$id/boards/$boardId"
              params={{ id, boardId }}
              className="rounded border border-border-strong px-4 py-2 font-medium hover:bg-surface-muted"
            >
              Cancel
            </Link>
          </div>
        </form>
      ) : null}

      {board && (
        <div className="border-t border-border pt-4">
          {deleteBoardMutation.error && (
            <ErrorBanner>{deleteBoardMutation.error.message}</ErrorBanner>
          )}
          <button
            onClick={handleDeleteBoard}
            disabled={deleteBoardMutation.isPending}
            className="rounded bg-danger px-4 py-2 font-medium text-on-primary hover:bg-danger-hover disabled:bg-fg-disabled"
          >
            Delete board
          </button>
        </div>
      )}
    </div>
  );
}
