import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { fetchPipeline, fetchPipelineRun } from "../../lib/pipelines";
import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { PipelineGraph } from "../../components/pipelines/PipelineGraph";
import type { Steps } from "../../components/pipelines/graph";
import { ErrorBanner } from "../../components/shared/ErrorBanner";
import { Loading } from "../../components/shared/Loading";

const RUN_TEXT: Record<string, string> = {
  PENDING: "text-fg-muted",
  RUNNING: "text-amber-600 dark:text-amber-400",
  SUCCESS: "text-green-600 dark:text-green-400",
  FAILURE: "text-danger",
};

export const Route = createFileRoute("/runs/$runId")({
  component: PipelineRunView,
});

function PipelineRunView() {
  const { runId } = Route.useParams();

  const { data: run, error } = useQuery({
    queryKey: ["runs", runId],
    queryFn: () => fetchPipelineRun(runId),
    // Keep polling until the run has finished, then stop.
    refetchInterval: (query) =>
      query.state.data?.status === "RUNNING" ||
      query.state.data?.status === "PENDING"
        ? 2000
        : false,
  });

  const { data: pipeline } = useQuery({
    queryKey: ["pipelines", run?.pipeline_id],
    queryFn: () => fetchPipeline(run!.pipeline_id),
    enabled: !!run,
  });

  useBreadcrumbs([
    { label: "Pipelines", to: "/pipelines" },
    { label: pipeline?.name ?? "" },
    { label: "Run" },
  ]);

  const statuses = useMemo(
    () =>
      Object.fromEntries(
        (run?.steps ?? []).map((step) => [step.step, step.status]),
      ),
    [run],
  );

  if (error) return <ErrorBanner>Run not found</ErrorBanner>;
  if (!run || !pipeline) return <Loading />;

  const steps: Steps = pipeline.steps;

  return (
    <div className="space-y-4 p-4">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold">{pipeline.name}</h1>
        <span className={`font-semibold ${RUN_TEXT[run.status] ?? ""}`}>
          {run.status}
        </span>
      </div>

      <PipelineGraph steps={steps} statuses={statuses} />

      <section className="space-y-2">
        <h2 className="text-lg font-semibold">Steps</h2>
        <ul className="space-y-1">
          {run.steps.map((step) => (
            <li
              key={step.step}
              className="flex flex-wrap items-center gap-3 text-sm"
            >
              <span className="font-medium">{step.step}</span>
              <span className={RUN_TEXT[step.status] ?? "text-fg-muted"}>
                {step.status}
              </span>
              {step.invocation_id && (
                <Link
                  to="/invocations/$id"
                  params={{ id: step.invocation_id }}
                  className="text-primary hover:underline"
                >
                  View invocation
                </Link>
              )}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
