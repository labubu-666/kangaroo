import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createPipeline } from "../../lib/pipelines";
import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import {
  PipelineForm,
  type PipelineFormValues,
} from "../../components/pipelines/PipelineForm";

export const Route = createFileRoute("/pipelines/create")({
  component: CreatePipeline,
});

function CreatePipeline() {
  useBreadcrumbs([{ label: "Pipelines", to: "/pipelines" }, { label: "New" }]);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (values: PipelineFormValues) =>
      createPipeline({
        name: values.name.trim(),
        description: values.description.trim() || undefined,
        steps: values.steps,
        labels: values.labels,
      }),
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey: ["pipelines"] });
      navigate({ to: "/pipelines/$id", params: { id: created.id } });
    },
  });

  return (
    <div className="space-y-4 p-4">
      <h1 className="text-2xl font-bold">Create pipeline</h1>
      <PipelineForm
        initial={{ name: "", description: "", steps: {}, labels: [] }}
        submitLabel="Create"
        pendingLabel="Creating..."
        disabled={mutation.isPending}
        error={mutation.error?.message ?? null}
        onSubmit={(values) => mutation.mutate(values)}
      />
    </div>
  );
}
