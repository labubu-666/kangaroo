import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery } from "@tanstack/react-query";
import { fetchFunction, runFunction } from "../../lib/functions";
import { fetchInvocation } from "../../lib/invocations";
import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { RunOutput } from "../../components/functions/RunOutput";
import { ErrorBanner } from "../../components/shared/ErrorBanner";
import { Loading } from "../../components/shared/Loading";

export const Route = createFileRoute("/invocations/$id")({
  component: InvocationDetail,
});

function InvocationDetail() {
  const { id } = Route.useParams();
  const navigate = useNavigate();

  const {
    data: invocation,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["invocations", id],
    queryFn: () => fetchInvocation(id),
  });

  const functionId = invocation?.function_id;
  const { data: fn } = useQuery({
    queryKey: ["functions", functionId],
    queryFn: () => fetchFunction(functionId!),
    enabled: !!functionId,
  });

  const rerunMutation = useMutation({
    mutationFn: () => runFunction(functionId!),
    onSuccess: (run) =>
      navigate({ to: "/invocations/$id", params: { id: run.id } }),
  });

  useBreadcrumbs([
    { label: "Functions", to: "/functions" },
    { label: "Invocations", to: "/functions", search: { tab: "invocations" } },
    { label: fn?.name ?? "Loading..." },
  ]);

  return (
    <div className="space-y-6 p-4">
      {error && <ErrorBanner>Error loading invocation</ErrorBanner>}

      {isLoading ? (
        <Loading />
      ) : invocation ? (
        <div className="space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h1 className="break-words text-2xl font-bold sm:text-3xl">
                {fn?.name ?? "Invocation"}
              </h1>
              <p className="mt-2 text-sm text-fg-muted">
                {new Date(invocation.created_at).toLocaleString()}
              </p>
              {fn && (
                <Link
                  to="/functions/$id"
                  params={{ id: fn.id }}
                  className="mt-2 inline-block text-sm text-primary hover:underline"
                >
                  Back to function
                </Link>
              )}
            </div>
            <button
              onClick={() => rerunMutation.mutate()}
              disabled={rerunMutation.isPending || !functionId}
              className="flex h-10 items-center gap-2 rounded bg-green-600 px-4 font-medium text-on-primary hover:bg-green-700 disabled:bg-fg-disabled"
            >
              <svg
                aria-hidden="true"
                viewBox="0 0 24 24"
                className="h-4 w-4 fill-current"
              >
                <path d="M8 5v14l11-7z" />
              </svg>
              {rerunMutation.isPending ? "Running..." : "Re-run"}
            </button>
          </div>

          {rerunMutation.error && (
            <ErrorBanner>{rerunMutation.error.message}</ErrorBanner>
          )}

          <RunOutput result={invocation} />
        </div>
      ) : null}
    </div>
  );
}
