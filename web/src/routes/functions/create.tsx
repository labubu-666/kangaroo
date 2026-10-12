import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createFunction } from "../../lib/functions";
import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { FunctionForm } from "../../components/functions/FunctionForm";

export const Route = createFileRoute("/functions/create")({
  component: CreateFunction,
});

function CreateFunction() {
  useBreadcrumbs([{ label: "Functions", to: "/functions" }, { label: "New" }]);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (values: {
      name: string;
      description: string;
      code: string;
      labels: string[];
    }) =>
      createFunction({
        name: values.name.trim(),
        description: values.description.trim() || undefined,
        code: values.code,
        labels: values.labels,
      }),
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey: ["functions"] });
      navigate({ to: "/functions/$id", params: { id: created.id } });
    },
  });

  return (
    <div className="space-y-4 p-4">
      <h1 className="text-2xl font-bold">Create function</h1>
      <FunctionForm
        initial={{ name: "", description: "", code: "", labels: [] }}
        submitLabel="Create"
        pendingLabel="Creating..."
        cancelTo="/functions"
        disabled={mutation.isPending}
        error={mutation.error?.message ?? null}
        onSubmit={(values) => mutation.mutate(values)}
      />
    </div>
  );
}
