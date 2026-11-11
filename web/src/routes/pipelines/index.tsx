import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import {
  fetchPipelines,
  fetchRuns,
  PIPELINE_LIMIT,
  RUN_LIMIT,
  type PipelineRun,
} from "../../lib/pipelines";
import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { FunctionList } from "../../components/functions/FunctionList";
import { ErrorBanner } from "../../components/shared/ErrorBanner";
import { Loading } from "../../components/shared/Loading";
import { Pagination } from "../../components/shared/Pagination";

type PipelinesTab = "pipelines" | "functions" | "runs";

export const Route = createFileRoute("/pipelines/")({
  component: PipelinesPage,
  validateSearch: (
    search: Record<string, unknown>,
  ): { tab?: PipelinesTab; pipeline_id?: string } => ({
    tab:
      search.tab === "runs" || search.tab === "functions"
        ? search.tab
        : "pipelines",
    ...(typeof search.pipeline_id === "string"
      ? { pipeline_id: search.pipeline_id }
      : {}),
  }),
});

const TABS: { value: PipelinesTab; label: string }[] = [
  { value: "pipelines", label: "Pipelines" },
  { value: "functions", label: "Functions" },
  { value: "runs", label: "Runs" },
];

function PipelinesPage() {
  const { tab = "pipelines", pipeline_id } = Route.useSearch();

  useBreadcrumbs([{ label: "Pipelines" }]);

  return (
    <div className="space-y-4 p-4">
      <div role="tablist" className="flex gap-4 border-b border-border">
        {TABS.map((t) => (
          <Link
            key={t.value}
            role="tab"
            aria-selected={tab === t.value}
            to="/pipelines"
            search={{ tab: t.value }}
            replace
            className={`-mb-px border-b-2 px-1 pb-2 font-semibold ${
              tab === t.value
                ? "border-primary text-primary"
                : "border-transparent text-fg-muted hover:text-fg"
            }`}
          >
            {t.label}
          </Link>
        ))}
      </div>

      {tab === "functions" && <FunctionList />}
      {tab === "runs" && <RunList pipelineId={pipeline_id} />}
      {tab === "pipelines" && <PipelineList />}
    </div>
  );
}

function PipelineList() {
  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState("");

  const { data, isLoading, error } = useQuery({
    queryKey: ["pipelines", offset, search],
    queryFn: () => fetchPipelines(PIPELINE_LIMIT, offset, search.trim()),
  });

  const items = data?.results ?? [];
  const total = data?.total ?? 0;

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
        <h2 className="text-xl font-semibold">Pipelines</h2>
        <Link
          to="/pipelines/create"
          className="rounded bg-primary px-4 py-2 text-center font-medium text-on-primary hover:bg-primary-hover"
        >
          New pipeline
        </Link>
      </div>

      <input
        type="search"
        aria-label="Search pipelines"
        placeholder="Search pipelines"
        value={search}
        onChange={(e) => {
          setSearch(e.target.value);
          setOffset(0);
        }}
        className="w-full rounded border border-border-strong px-3 py-2"
      />

      {error && <ErrorBanner>Error loading pipelines</ErrorBanner>}

      {isLoading ? (
        <Loading />
      ) : items.length === 0 ? (
        <div className="text-center text-fg-muted">
          {search.trim()
            ? "No pipelines match this search"
            : "No pipelines yet"}
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {items.map((pipeline) => (
            <Link
              key={pipeline.id}
              to="/pipelines/$id"
              params={{ id: pipeline.id }}
              className="flex flex-col gap-1 rounded border border-border p-4 hover:border-primary hover:bg-primary-subtle transition"
            >
              <h3 className="font-semibold text-primary">{pipeline.name}</h3>
              {pipeline.description && (
                <p className="text-sm text-fg-secondary">
                  {pipeline.description}
                </p>
              )}
            </Link>
          ))}
        </div>
      )}

      <Pagination
        offset={offset}
        limit={PIPELINE_LIMIT}
        total={total}
        disabled={isLoading}
        onChange={setOffset}
      />
    </div>
  );
}

function RunList({ pipelineId }: { pipelineId?: string }) {
  const [offset, setOffset] = useState(0);

  const { data, isLoading, error } = useQuery({
    queryKey: ["runs", pipelineId ?? null, offset],
    queryFn: () => fetchRuns(RUN_LIMIT, offset, pipelineId),
    refetchInterval: 2000,
  });

  const items: PipelineRun[] = data?.results ?? [];
  const total = data?.total ?? 0;

  const { data: pipelines } = useQuery({
    queryKey: ["pipelines", "names"],
    queryFn: () => fetchPipelines(100, 0),
  });
  const names = new Map(
    (pipelines?.results ?? []).map((pipeline) => [pipeline.id, pipeline.name]),
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-semibold">Runs</h2>
        {pipelineId && (
          <Link
            to="/pipelines"
            search={{ tab: "runs" }}
            className="text-sm text-primary hover:underline"
          >
            Show all runs
          </Link>
        )}
      </div>

      {error && <ErrorBanner>Error loading runs</ErrorBanner>}

      {isLoading ? (
        <Loading />
      ) : items.length === 0 ? (
        <div className="text-center text-fg-muted">No runs yet</div>
      ) : (
        <div className="flex flex-col gap-3">
          {items.map((run) => (
            <Link
              key={run.id}
              to="/runs/$runId"
              params={{ runId: run.id }}
              className="flex flex-wrap items-center justify-between gap-2 rounded border border-border p-3 hover:border-primary hover:bg-primary-subtle transition"
            >
              <span className="font-medium">
                {names.get(run.pipeline_id) ?? "Unknown pipeline"}
              </span>
              <span className="text-sm">{run.status}</span>
              <span className="text-xs text-fg-muted">
                {new Date(run.created_at).toLocaleString()}
              </span>
            </Link>
          ))}
        </div>
      )}

      <Pagination
        offset={offset}
        limit={RUN_LIMIT}
        total={total}
        disabled={isLoading}
        onChange={setOffset}
      />
    </div>
  );
}
