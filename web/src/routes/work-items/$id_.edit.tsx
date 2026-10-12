import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { fetchWorkItem, updateWorkItem } from "../../lib/work-items";
import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { useGoBackOr } from "../../lib/navigation";
import { projectFilter } from "../../lib/filter-bubbles";

import { ErrorBanner } from "../../components/shared/ErrorBanner";
import { Loading } from "../../components/shared/Loading";

export const Route = createFileRoute("/work-items/$id_/edit")({
  component: EditWorkItem,
});

interface WorkItemForm {
  title: string;
  description: string;
}

function EditWorkItem() {
  const { id } = Route.useParams();
  const navigate = useNavigate();
  const goBackOr = useGoBackOr();
  const queryClient = useQueryClient();

  const {
    data: item,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["work-items", id],
    queryFn: () => fetchWorkItem(id),
  });

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    setError,
  } = useForm<WorkItemForm>({
    values: item
      ? { title: item.title, description: item.description ?? "" }
      : undefined,
  });

  const mutation = useMutation({
    mutationFn: (data: WorkItemForm) =>
      updateWorkItem(id, {
        title: data.title.trim(),
        description: data.description.trim() || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["work-items"] });
      goBackOr(() => navigate({ to: "/work-items/$id", params: { id } }));
    },
    onError: (err) => {
      setError("root", {
        message: err.message,
      });
    },
  });

  const onSubmit = (data: WorkItemForm) => {
    if (!data.title.trim()) {
      setError("title", { message: "Title is required" });
      return;
    }
    mutation.mutate(data);
  };

  useBreadcrumbs([
    {
      label: "Work items",
      to: "/work-items",
      search: { filter: projectFilter(item?.project_id) },
    },
    {
      label: item?.title ?? "Loading...",
      to: "/work-items/$id",
      params: { id },
    },
    { label: "Edit" },
  ]);

  return (
    <div className="space-y-6 p-4">
      {error && <ErrorBanner>Error loading work item</ErrorBanner>}

      {isLoading ? (
        <Loading />
      ) : item ? (
        <form
          onSubmit={handleSubmit(onSubmit)}
          autoComplete="off"
          className="space-y-4 rounded border border-gray-200 p-4"
        >
          {errors.root && <ErrorBanner>{errors.root.message}</ErrorBanner>}

          <div className="space-y-2">
            <label htmlFor="title" className="block font-medium">
              Title *
            </label>
            <input
              id="title"
              type="text"
              disabled={mutation.isPending}
              placeholder="Enter work item title"
              className="w-full rounded border border-gray-300 px-3 py-2"
              {...register("title", { required: "Title is required" })}
            />
            {errors.title && (
              <p className="text-sm text-red-600">{errors.title.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <label htmlFor="description" className="block font-medium">
              Description
            </label>
            <textarea
              id="description"
              disabled={mutation.isPending}
              placeholder="Enter work item description (optional)"
              rows={4}
              className="w-full rounded border border-gray-300 px-3 py-2"
              {...register("description")}
            />
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              type="submit"
              disabled={mutation.isPending || !isDirty}
              className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:bg-gray-400"
            >
              {mutation.isPending ? "Saving..." : "Save"}
            </button>
            <Link
              to="/work-items/$id"
              params={{ id }}
              className="rounded border border-gray-300 px-4 py-2 font-medium hover:bg-gray-50"
            >
              Cancel
            </Link>
          </div>
        </form>
      ) : null}
    </div>
  );
}
