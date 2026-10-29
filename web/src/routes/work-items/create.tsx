import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { createWorkItem, type WorkItemCreate } from "../../lib/work-items";
import { fetchWorkItemTypes } from "../../lib/workflow";
import { useProjectOptions } from "../../lib/projects";
import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { ErrorBanner } from "../../components/shared/ErrorBanner";
import { LabelsEditor } from "../../components/shared/LabelsEditor";
import { projectFilter } from "../../lib/filter-bubbles";

export const Route = createFileRoute("/work-items/create")({
  component: CreateWorkItem,
  validateSearch: (
    search: Record<string, unknown>,
  ): { projectId?: string; parentId?: string } => ({
    projectId:
      typeof search.projectId === "string" ? search.projectId : undefined,
    parentId: typeof search.parentId === "string" ? search.parentId : undefined,
  }),
});

interface WorkItemForm {
  summary: string;
  description: string;
  projectId: string;
  typeId: string;
}

function CreateWorkItem() {
  const { projectId: initialProjectId, parentId } = Route.useSearch();
  useBreadcrumbs([
    {
      label: "Work items",
      to: "/work-items",
      search: { filter: projectFilter(initialProjectId) },
    },
    { label: "New" },
  ]);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [labels, setLabels] = useState<string[]>([]);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
    getValues,
    setValue,
    watch,
  } = useForm<WorkItemForm>({
    defaultValues: {
      summary: "",
      description: "",
      projectId: initialProjectId ?? "",
      typeId: "",
    },
  });

  // The type and status choices come from the selected project
  const projectId = watch("projectId");
  const { data: types } = useQuery({
    queryKey: ["work-item-types", projectId],
    queryFn: () => fetchWorkItemTypes(projectId),
    enabled: !!projectId,
  });
  // A subtask is made under a parent, so only standard types are offered on a task
  const offeredTypes = (types ?? []).filter((t) =>
    parentId ? t.level === "subtask" : t.level === "standard",
  );
  const firstOfferedType = offeredTypes[0]?.id;
  useEffect(() => {
    if (firstOfferedType && !getValues("typeId")) {
      setValue("typeId", firstOfferedType);
    }
  }, [firstOfferedType, getValues, setValue]);

  const { data: projects } = useProjectOptions();
  const hasProjects = (projects?.results ?? []).length > 0;

  useEffect(() => {
    const firstProject = projects?.results[0];
    if (firstProject && !getValues("projectId")) {
      setValue("projectId", firstProject.id);
    }
  }, [projects, getValues, setValue]);

  const mutation = useMutation({
    mutationFn: (data: WorkItemCreate) => createWorkItem(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["work-items"] });
      if (parentId) {
        navigate({ to: "/work-items/$id", params: { id: parentId } });
      } else {
        navigate({
          to: "/projects/$id",
          params: { id: getValues("projectId") },
          search: { tab: "work-items" },
        });
      }
    },
    onError: (err) => {
      setError("root", {
        message: err.message,
      });
    },
  });

  const onSubmit = (data: WorkItemForm) => {
    if (!data.summary.trim()) {
      setError("summary", { message: "Summary is required" });
      return;
    }

    if (!data.typeId) {
      setError("typeId", { message: "Type is required" });
      return;
    }

    mutation.mutate({
      summary: data.summary.trim(),
      description: data.description.trim() || undefined,
      project_id: data.projectId,
      type_id: data.typeId,
      parent_id: parentId,
      labels,
    });
  };

  return (
    <div className="space-y-4 p-4">
      <div className="flex items-center gap-4">
        <h1 className="text-2xl font-bold">
          {parentId ? "Create subtask" : "Create work item"}
        </h1>
      </div>

      {errors.root && <ErrorBanner>{errors.root.message}</ErrorBanner>}

      <form
        onSubmit={handleSubmit(onSubmit)}
        autoComplete="off"
        className="space-y-4 rounded border border-border p-4"
      >
        <div className="space-y-2">
          <label htmlFor="summary" className="block font-medium">
            Summary *
          </label>
          <input
            id="summary"
            type="text"
            disabled={mutation.isPending}
            placeholder="Enter work item summary"
            className="w-full rounded border border-border-strong px-3 py-2"
            {...register("summary", { required: "Summary is required" })}
          />
          {errors.summary && (
            <p className="text-sm text-danger">{errors.summary.message}</p>
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
            className="w-full rounded border border-border-strong px-3 py-2"
            {...register("description")}
          />
        </div>

        <div className="space-y-2">
          <label htmlFor="project" className="block font-medium">
            Project
          </label>
          {hasProjects ? (
            <select
              id="project"
              disabled={mutation.isPending}
              className="w-full rounded border border-border-strong px-3 py-2"
              {...register("projectId", { required: "Project is required" })}
            >
              {projects?.results.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          ) : (
            <p className="text-sm text-fg-secondary">
              Create a project first before adding work items.
            </p>
          )}
        </div>

        <div className="space-y-2">
          <label htmlFor="type" className="block font-medium">
            Type
          </label>
          <select
            id="type"
            disabled={mutation.isPending || offeredTypes.length === 0}
            className="w-full rounded border border-border-strong px-3 py-2"
            {...register("typeId", { required: "Type is required" })}
          >
            {offeredTypes.map((type) => (
              <option key={type.id} value={type.id}>
                {type.name}
              </option>
            ))}
          </select>
          {errors.typeId && (
            <p className="text-sm text-danger">{errors.typeId.message}</p>
          )}
        </div>

        <LabelsEditor
          labels={labels}
          onChange={setLabels}
          disabled={mutation.isPending}
        />

        <div className="flex flex-wrap gap-3">
          <button
            type="submit"
            disabled={mutation.isPending || !hasProjects}
            className="rounded bg-primary px-4 py-2 font-medium text-on-primary hover:bg-primary-hover disabled:bg-fg-disabled"
          >
            {mutation.isPending ? "Creating..." : "Create"}
          </button>
          <Link
            to="/work-items"
            className="rounded border border-border-strong px-4 py-2 font-medium hover:bg-surface-muted"
          >
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}
