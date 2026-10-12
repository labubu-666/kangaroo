import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { createBoard } from "../../lib/boards";
import { fetchProject } from "../../lib/projects";
import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { ErrorBanner } from "../../components/shared/ErrorBanner";

export const Route = createFileRoute("/projects/$id_/boards/create")({
  component: CreateBoard,
});

interface BoardForm {
  name: string;
  description: string;
  filter: string;
}

function CreateBoard() {
  const { id } = Route.useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: project } = useQuery({
    queryKey: ["projects", id],
    queryFn: () => fetchProject(id),
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
  } = useForm<BoardForm>({
    defaultValues: { name: "", description: "", filter: "" },
  });

  const mutation = useMutation({
    mutationFn: (data: BoardForm) =>
      createBoard({
        name: data.name.trim(),
        description: data.description.trim() || undefined,
        project_id: id,
        filter: data.filter.trim() || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["boards"] });
      navigate({ to: "/projects/$id", params: { id } });
    },
    onError: (err) => {
      setError("root", {
        message: err.message,
      });
    },
  });

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
    { label: "New board" },
  ]);

  return (
    <div className="space-y-4 p-4">
      <div className="flex items-center gap-4">
        <h1 className="text-2xl font-bold">Create board</h1>
      </div>

      {errors.root && <ErrorBanner>{errors.root.message}</ErrorBanner>}

      <form
        onSubmit={handleSubmit(onSubmit)}
        autoComplete="off"
        className="space-y-4 rounded border border-gray-200 p-4"
      >
        <div className="space-y-2">
          <label htmlFor="name" className="block font-medium">
            Name *
          </label>
          <input
            id="name"
            type="text"
            disabled={mutation.isPending}
            placeholder="Enter board name"
            className="w-full rounded border border-gray-300 px-3 py-2"
            {...register("name", { required: "Name is required" })}
          />
          {errors.name && (
            <p className="text-sm text-red-600">{errors.name.message}</p>
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
            className="w-full rounded border border-gray-300 px-3 py-2 font-mono"
            {...register("filter")}
          />
          <p className="text-sm text-gray-500">
            Narrows the project's work items. Text fields: title, description,
            status, type, parent_id, project.id, project.name. List field:
            labels. Text operators: ==, !=, ~ (contains text), in [...], not in
            [...]. List operators: contains 'a' (has it), contains [...] (has
            all), in [...] (has any), not in [...] (has none), ~ (label contains
            text), is empty, is not empty. Combine with and, or, not and
            parentheses. Leave empty to show all work items in the project. See
            docs/filter-language.md for details.
          </p>
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
            className="w-full rounded border border-gray-300 px-3 py-2"
            {...register("description")}
          />
        </div>

        <div className="flex flex-wrap gap-3">
          <button
            type="submit"
            disabled={mutation.isPending}
            className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:bg-gray-400"
          >
            {mutation.isPending ? "Creating..." : "Create"}
          </button>
          <Link
            to="/projects/$id"
            params={{ id }}
            className="rounded border border-gray-300 px-4 py-2 font-medium hover:bg-gray-50"
          >
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}
