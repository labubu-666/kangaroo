import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  deleteFunction,
  fetchFunction,
  runFunction,
} from "../../lib/functions";
import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { ErrorBanner } from "../../components/shared/ErrorBanner";
import { Loading } from "../../components/shared/Loading";

export const Route = createFileRoute("/functions/$id")({
  component: FunctionDetail,
});

function FunctionDetail() {
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

  const runMutation = useMutation({
    mutationFn: () => runFunction(id),
    onSuccess: (invocation) =>
      navigate({ to: "/invocations/$id", params: { id: invocation.id } }),
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteFunction(id),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: ["functions", id] });
      queryClient.invalidateQueries({ queryKey: ["functions"] });
      navigate({ to: "/functions" });
    },
  });

  const handleDelete = () => {
    if (confirm("Are you sure you want to delete this function?")) {
      deleteMutation.mutate();
    }
  };

  useBreadcrumbs([
    { label: "Functions", to: "/functions" },
    { label: fn?.name ?? "Loading..." },
  ]);

  return (
    <div className="space-y-6 p-4">
      {error && <ErrorBanner>Error loading function</ErrorBanner>}

      {isLoading ? (
        <Loading />
      ) : fn ? (
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              <h1 className="break-words text-2xl font-bold sm:text-3xl">
                {fn.name}
              </h1>
              {fn.description && (
                <p className="mt-2 whitespace-pre-wrap text-gray-600">
                  {fn.description}
                </p>
              )}
              {fn.labels.length > 0 && (
                <ul className="mt-2 flex flex-wrap gap-2">
                  {fn.labels.map((label) => (
                    <li
                      key={label}
                      className="rounded bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-700"
                    >
                      {label}
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => runMutation.mutate()}
                disabled={runMutation.isPending}
                className="rounded bg-green-600 px-4 py-2 font-medium text-white hover:bg-green-700 disabled:bg-gray-400"
              >
                {runMutation.isPending ? "Running..." : "Run"}
              </button>
              <Link
                to="/functions/$id/edit"
                params={{ id: fn.id }}
                className="rounded border border-gray-300 px-4 py-2 font-medium hover:bg-gray-50"
              >
                Edit
              </Link>
              <button
                onClick={handleDelete}
                disabled={deleteMutation.isPending}
                className="rounded bg-red-600 px-4 py-2 font-medium text-white hover:bg-red-700 disabled:bg-gray-400"
              >
                Delete
              </button>
            </div>
          </div>

          {runMutation.error && (
            <ErrorBanner>{runMutation.error.message}</ErrorBanner>
          )}
          {deleteMutation.error && (
            <ErrorBanner>{deleteMutation.error.message}</ErrorBanner>
          )}

          <div>
            <h2 className="mb-2 font-semibold text-gray-700">Code</h2>
            <pre className="overflow-x-auto whitespace-pre rounded border border-gray-200 bg-gray-50 p-4 font-mono text-sm">
              {fn.code}
            </pre>
          </div>
        </div>
      ) : null}
    </div>
  );
}
