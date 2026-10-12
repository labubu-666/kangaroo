import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchFunction, updateFunction } from "../../lib/functions";
import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { FunctionForm } from "../../components/functions/FunctionForm";
import { Loading } from "../../components/shared/Loading";

export const Route = createFileRoute("/functions/$id_/edit")({
  component: EditFunction,
});

function EditFunction() {
  const { id } = Route.useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const {
    data: fn,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["functions", id],
    queryFn: () => fetchFunction(id),
  });

  const mutation = useMutation({
    mutationFn: (values: {
      name: string;
      description: string;
      code: string;
      labels: string[];
    }) =>
      updateFunction(id, {
        name: values.name.trim(),
        description: values.description.trim() || null,
        code: values.code,
        labels: values.labels,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["functions"] });
      navigate({ to: "/functions/$id", params: { id } });
    },
  });

  useBreadcrumbs([
    { label: "Functions", to: "/functions" },
    { label: fn?.name ?? "Loading...", to: "/functions/$id", params: { id } },
    { label: "Edit" },
  ]);

  return (
    <div className="space-y-4 p-4">
      <h1 className="text-2xl font-bold">Edit function</h1>
      {error && <p className="text-red-600">Error loading function</p>}
      {isLoading ? (
        <Loading />
      ) : fn ? (
        <FunctionForm
          initial={{
            name: fn.name,
            description: fn.description ?? "",
            code: fn.code,
            labels: fn.labels,
          }}
          submitLabel="Save"
          pendingLabel="Saving..."
          cancelTo="/functions/$id"
          cancelParams={{ id }}
          disabled={mutation.isPending}
          error={mutation.error?.message ?? null}
          onSubmit={(values) => mutation.mutate(values)}
        />
      ) : null}
    </div>
  );
}
