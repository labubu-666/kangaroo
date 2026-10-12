import { Link, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { createProject } from "../../lib/projects";
import { fetchProjectTemplates } from "../../lib/project-templates";
import { useBreadcrumbs } from "../breadcrumbs/BreadcrumbsContext";
import { ErrorBanner } from "../shared/ErrorBanner";

interface ProjectForm {
  name: string;
  description: string;
  template: string;
}

export function CreateProjectForm() {
  useBreadcrumbs([{ label: "Projects", to: "/projects" }, { label: "New" }]);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
    setValue,
  } = useForm<ProjectForm>({
    defaultValues: { name: "", description: "", template: "" },
  });

  const { data: templates, error: templatesError } = useQuery({
    queryKey: ["project-templates"],
    queryFn: fetchProjectTemplates,
  });

  // The server names the default template; select it until the user picks another
  const defaultTemplate = templates?.default;
  useEffect(() => {
    if (defaultTemplate) setValue("template", defaultTemplate);
  }, [defaultTemplate, setValue]);

  const mutation = useMutation({
    mutationFn: (data: ProjectForm) =>
      createProject({
        name: data.name.trim(),
        description: data.description.trim() || undefined,
        template: data.template,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      navigate({ to: "/projects" });
    },
    onError: (err) => {
      setError("root", {
        message: err.message,
      });
    },
  });

  const onSubmit = (data: ProjectForm) => {
    if (!data.name.trim()) {
      setError("name", { message: "Name is required" });
      return;
    }
    mutation.mutate(data);
  };

  return (
    <div className="space-y-4 p-4">
      <div className="flex items-center gap-4">
        <h1 className="text-2xl font-bold">Create project</h1>
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
            placeholder="Enter project name"
            className="w-full rounded border border-gray-300 px-3 py-2"
            {...register("name", { required: "Name is required" })}
          />
          {errors.name && (
            <p className="text-sm text-red-600">{errors.name.message}</p>
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
            className="w-full rounded border border-gray-300 px-3 py-2"
            {...register("description")}
          />
        </div>

        <div className="space-y-2">
          <label htmlFor="template" className="block font-medium">
            Template *
          </label>
          <select
            id="template"
            disabled={mutation.isPending || !templates}
            className="w-full rounded border border-gray-300 px-3 py-2"
            {...register("template", { required: "Template is required" })}
          >
            {(templates?.names ?? []).map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
          {templatesError && (
            <p className="text-sm text-red-600">Error loading templates</p>
          )}
          {errors.template && (
            <p className="text-sm text-red-600">{errors.template.message}</p>
          )}
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
            to="/projects"
            className="rounded border border-gray-300 px-4 py-2 font-medium hover:bg-gray-50"
          >
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}
