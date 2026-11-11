import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useId, useRef, useState } from "react";
import { fetchFunctions } from "../../lib/functions";
import {
  deletePipeline,
  fetchPipeline,
  startPipelineRun,
  updatePipeline,
  type PipelineCreate,
} from "../../lib/pipelines";
import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { InlineEdit } from "../../components/InlineEdit";
import { RunButton } from "../../components/functions/RunButton";
import type { Steps } from "../../components/pipelines/graph";
import {
  PipelineEditor,
  type PipelineEditorHandle,
} from "../../components/pipelines/PipelineEditor";
import { ErrorBanner } from "../../components/shared/ErrorBanner";
import { Loading } from "../../components/shared/Loading";
import { removeRecent, useRecordRecent } from "../../lib/recent";
import { useDismiss } from "../../lib/use-dismiss";

function sameSteps(a: Steps, b: Steps): boolean {
  const names = Object.keys(a).sort();
  if (names.length !== Object.keys(b).length) return false;
  return names.every(
    (name) =>
      b[name] !== undefined &&
      a[name].function_id === b[name].function_id &&
      JSON.stringify(a[name].on_success) ===
        JSON.stringify(b[name].on_success) &&
      JSON.stringify(a[name].on_failure) === JSON.stringify(b[name].on_failure),
  );
}

export const Route = createFileRoute("/pipelines/$id")({
  component: PipelineDetail,
});

function PipelineDetail() {
  const { id } = Route.useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuId = useId();
  const menuRef = useDismiss<HTMLDivElement>(menuOpen, () =>
    setMenuOpen(false),
  );
  const editorRef = useRef<PipelineEditorHandle>(null);

  const {
    data: pipeline,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["pipelines", id],
    queryFn: () => fetchPipeline(id),
  });

  const { data: functions } = useQuery({
    queryKey: ["functions", "names"],
    queryFn: () => fetchFunctions(100, 0),
  });

  useBreadcrumbs([
    { label: "Pipelines", to: "/pipelines" },
    { label: pipeline?.name ?? "" },
  ]);

  useRecordRecent(
    pipeline
      ? {
          type: "pipeline",
          id: pipeline.id,
          title: pipeline.name,
          to: "/pipelines/$id",
          params: { id: pipeline.id },
        }
      : undefined,
  );

  const runMutation = useMutation({
    mutationFn: () => startPipelineRun(id),
    onSuccess: ({ run_id }) =>
      navigate({ to: "/runs/$runId", params: { runId: run_id } }),
  });

  // Saves the whole pipeline, so every field not in `changes` keeps its saved value.
  const save = (changes: Partial<PipelineCreate>) => {
    if (!pipeline) throw new Error("Pipeline not loaded");
    return updatePipeline(id, {
      name: pipeline.name,
      description: pipeline.description ?? undefined,
      steps: pipeline.steps,
      labels: pipeline.labels,
      ...changes,
    }).then((updated) => {
      queryClient.setQueryData(["pipelines", id], updated);
      queryClient.invalidateQueries({ queryKey: ["pipelines"] });
    });
  };

  const stepsMutation = useMutation({
    mutationFn: (steps: Steps) => save({ steps }),
  });

  // The canvas reports on mount too, so skip steps that match what is saved.
  // Sorting keys first means key order from the server cannot look like a change.
  const handleStepsChange = useCallback(
    (steps: Steps) => {
      if (!pipeline || sameSteps(steps, pipeline.steps)) return;
      stepsMutation.mutate(steps);
    },
    [pipeline, stepsMutation.mutate],
  );

  const deleteMutation = useMutation({
    mutationFn: () => deletePipeline(id),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: ["pipelines", id] });
      removeRecent("pipeline", id);
      queryClient.invalidateQueries({ queryKey: ["pipelines"] });
      navigate({ to: "/pipelines" });
    },
  });

  const handleDelete = () => {
    setMenuOpen(false);
    if (confirm("Are you sure you want to delete this pipeline?")) {
      deleteMutation.mutate();
    }
  };

  if (isLoading) return <Loading />;
  if (error) return <ErrorBanner>Pipeline not found</ErrorBanner>;
  if (!pipeline) return null;

  // A function can be added again, so every saved function stays in the panel.
  const available = functions?.results ?? [];

  return (
    <div className="space-y-6 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <InlineEdit
            value={pipeline.name}
            onSave={(name) => save({ name: name.trim() })}
            ariaLabel="name"
            placeholder="Enter pipeline name"
            requiredMessage="Name is required"
            textClassName="h-10 text-2xl font-bold sm:text-3xl"
          >
            <h1 className="flex h-10 cursor-pointer items-center break-words text-2xl font-bold sm:text-3xl">
              {pipeline.name}
            </h1>
          </InlineEdit>
          {pipeline.description && (
            <p className="text-fg-secondary">{pipeline.description}</p>
          )}
        </div>
        <div className="flex flex-wrap gap-3">
          <RunButton
            onClick={() => runMutation.mutate()}
            disabled={runMutation.isPending}
          >
            {runMutation.isPending ? "Starting..." : "Run"}
          </RunButton>
          <div ref={menuRef} className="relative">
            <button
              type="button"
              aria-label="More actions"
              aria-haspopup="menu"
              aria-expanded={menuOpen}
              aria-controls={menuId}
              onClick={() => setMenuOpen((open) => !open)}
              className="flex h-10 items-center rounded border border-border-strong px-4 font-medium hover:bg-surface-muted"
            >
              ⋯
            </button>
            {menuOpen && (
              <div
                id={menuId}
                role="menu"
                aria-label="Pipeline actions"
                className="absolute right-0 z-10 mt-2 flex min-w-40 flex-col rounded border border-border bg-surface py-1 shadow-lg"
              >
                <Link
                  role="menuitem"
                  to="/pipelines"
                  search={{ tab: "runs", pipeline_id: pipeline.id }}
                  onClick={() => setMenuOpen(false)}
                  className="px-3 py-2 text-left font-medium hover:bg-surface-strong"
                >
                  Last runs
                </Link>
                <button
                  type="button"
                  role="menuitem"
                  onClick={handleDelete}
                  disabled={deleteMutation.isPending}
                  className="px-3 py-2 text-left font-medium text-danger hover:bg-surface-strong disabled:text-fg-disabled"
                >
                  Delete
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {runMutation.error && (
        <ErrorBanner>{runMutation.error.message}</ErrorBanner>
      )}
      {stepsMutation.error && (
        <ErrorBanner>{stepsMutation.error.message}</ErrorBanner>
      )}

      <div className="flex flex-col gap-4 md:flex-row">
        <section className="min-w-0 flex-1 space-y-3">
          <p className="text-sm text-fg-muted">
            Drag from a step&apos;s green handle to set what runs on success,
            and from its red handle to set what runs on failure. Steps with no
            handle connected end the run. Use a step&apos;s × to remove it.
            Changes save as you make them.
          </p>
          <PipelineEditor
            ref={editorRef}
            initialSteps={pipeline.steps}
            disabled={false}
            onChange={handleStepsChange}
          />
        </section>
        <aside
          aria-label="Functions"
          className="flex w-full shrink-0 flex-col gap-2 rounded border border-border p-3 md:w-64"
        >
          <h2 className="font-semibold">Functions</h2>
          {available.length === 0 ? (
            <p className="text-sm text-fg-muted">No functions saved</p>
          ) : (
            <ul className="flex flex-col gap-1">
              {available.map((fn) => (
                <li key={fn.id}>
                  <button
                    type="button"
                    onClick={() => editorRef.current?.addStep(fn.id, fn.name)}
                    className="w-full truncate rounded px-2 py-1.5 text-left hover:bg-surface-strong"
                  >
                    {fn.name}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </aside>
      </div>
    </div>
  );
}
