import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { fetchFunction } from "../../lib/functions";
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
          <div>
            <h1 className="break-words text-2xl font-bold sm:text-3xl">
              {fn?.name ?? "Invocation"}
            </h1>
            <p className="mt-2 text-sm text-gray-500">
              {new Date(invocation.created_at).toLocaleString()}
            </p>
            {fn && (
              <Link
                to="/functions/$id"
                params={{ id: fn.id }}
                className="mt-2 inline-block text-sm text-blue-600 hover:underline"
              >
                Back to function
              </Link>
            )}
          </div>

          <RunOutput result={invocation} />
        </div>
      ) : null}
    </div>
  );
}
