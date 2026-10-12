import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { useState } from "react";

// A delete the API refused until a replacement is chosen
type Pending =
  | { kind: "status"; item: ProjectStatus; count: number }
  | { kind: "type"; item: WorkItemType; count: number };
import { fetchProject } from "../../lib/projects";
import { useBreadcrumbs } from "../breadcrumbs/BreadcrumbsContext";
import { ReplacementDialog } from "./ReplacementDialog";
import { ConfirmChange } from "./ConfirmChange";
import {
  CATEGORY_LABELS,
  StatusSection,
  TransitionSection,
  TypeSection,
} from "./WorkflowSections";
import {
  deleteStatus,
  deleteWorkItemType,
  fetchStatuses,
  fetchTransitions,
  fetchWorkItemTypes,
  type ProjectStatus,
  type WorkItemType,
} from "../../lib/workflow";
import { ErrorBanner } from "../shared/ErrorBanner";
import { fetchBoards } from "../../lib/boards";
import { boardsUsingStatusName } from "../../lib/rename-warning";
import { fetchWorkItems } from "../../lib/work-items";
import { updateStatus, type StatusCategory } from "../../lib/workflow";
import { Loading } from "../shared/Loading";

export function WorkflowPage({ projectId: id }: { projectId: string }) {
  const queryClient = useQueryClient();
  const [pending, setPending] = useState<Pending | null>(null);
  const [dialogError, setDialogError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  // A status change waiting for the user to confirm its side effects
  const [confirming, setConfirming] = useState<{
    status: ProjectStatus;
    kind: "rename" | "category";
    newName?: string;
    newCategory?: StatusCategory;
    lines: string[];
  } | null>(null);

  const { data: project, isLoading } = useQuery({
    queryKey: ["projects", id],
    queryFn: () => fetchProject(id),
  });

  const { data: statuses = [], error: statusesError } = useQuery({
    queryKey: ["statuses", id],
    queryFn: () => fetchStatuses(id),
  });

  const { data: types = [], error: typesError } = useQuery({
    queryKey: ["work-item-types", id],
    queryFn: () => fetchWorkItemTypes(id),
  });

  const { data: transitions = [] } = useQuery({
    queryKey: ["status-transitions", id],
    queryFn: () => fetchTransitions(id),
  });

  useBreadcrumbs([
    { label: "Projects", to: "/projects" },
    {
      label: project?.name ?? "Loading...",
      to: "/projects/$id",
      params: { id },
    },
    { label: "Statuses and types" },
  ]);

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["statuses", id] });
    queryClient.invalidateQueries({ queryKey: ["work-item-types", id] });
    queryClient.invalidateQueries({ queryKey: ["status-transitions", id] });
    queryClient.invalidateQueries({ queryKey: ["work-items"] });
    queryClient.invalidateQueries({ queryKey: ["work-item-types"] });
  };

  // Runs a change (create, rename, reorder, transition) and refreshes the page
  const runAction = (action: () => Promise<unknown>) => {
    setMessage(null);
    action()
      .then(refresh)
      .catch((err: Error) => setMessage(err.message));
  };

  // Deletes a status or type. The API refuses a status or type that work items
  // use, and the reply says how many. That opens the replacement dialog.
  const deleteItem = useMutation({
    mutationFn: ({
      kind,
      id: itemId,
      replacementId,
    }: {
      kind: "status" | "type";
      id: string;
      replacementId?: string;
    }) =>
      kind === "status"
        ? deleteStatus(itemId, replacementId)
        : deleteWorkItemType(itemId, replacementId),
    onSuccess: () => {
      setPending(null);
      setDialogError(null);
      setMessage(null);
      refresh();
    },
    onError: (err, vars) => {
      if (vars.replacementId) {
        setDialogError(err.message);
        return;
      }
      const match = /^(\d+) work items use this/.exec(err.message);
      const list: { id: string }[] = vars.kind === "status" ? statuses : types;
      const item = list.find((candidate) => candidate.id === vars.id);
      if (match && item) {
        setPending({
          kind: vars.kind,
          item: item as ProjectStatus & WorkItemType,
          count: Number(match[1]),
        });
        return;
      }
      setMessage(err.message);
    },
  });

  const requestDelete = (kind: "status" | "type", itemId: string) => {
    setMessage(null);
    deleteItem.mutate({ kind, id: itemId });
  };

  const confirmReplacement = (replacementId: string) => {
    if (!pending) return;
    setDialogError(null);
    deleteItem.mutate({
      kind: pending.kind,
      id: pending.item.id,
      replacementId,
    });
  };

  // A rename breaks any saved board filter that names the old status name.
  // Those boards are listed before the rename is saved.
  const prepareRename = async (status: ProjectStatus, newName: string) => {
    setMessage(null);
    if (newName === status.name) return;
    const boards = await fetchBoards(100, 0, { projectId: id }).then(
      (page) => page.results,
    );
    const affected = boardsUsingStatusName(boards, status.name);
    if (affected.length === 0) {
      applyStatusChange(status.id, { name: newName });
      return;
    }
    setConfirming({
      status,
      kind: "rename",
      newName,
      lines: [
        `Renaming “${status.name}” to “${newName}” stops these saved board filters from matching:`,
        ...affected.map(
          (board) => `Board “${board.name}” uses ${board.filter}`,
        ),
      ],
    });
  };

  // A category change moves the status's work items to the new category.
  // Their count is shown before the change is saved.
  const prepareCategory = async (
    status: ProjectStatus,
    next: StatusCategory,
  ) => {
    setMessage(null);
    const page = await fetchWorkItems(1, 0, {
      filter: `status == '${status.id}'`,
      trashed: "all",
    });
    const count = page.total;
    if (count === 0) {
      applyStatusChange(status.id, { category: next });
      return;
    }
    setConfirming({
      status,
      kind: "category",
      newCategory: next,
      lines: [
        `${count} work ${count === 1 ? "item" : "items"} in “${status.name}” will change from ${CATEGORY_LABELS[status.category]} to ${CATEGORY_LABELS[next]}.`,
      ],
    });
  };

  const applyStatusChange = (
    statusId: string,
    change: { name?: string; category?: StatusCategory },
  ) => {
    setConfirming(null);
    runAction(() => updateStatus(statusId, change));
  };

  const doneCount = statuses.filter((s) => s.category === "done").length;

  return (
    <div className="space-y-8 p-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-bold">Statuses and types</h1>
        <Link
          to="/projects/$id"
          params={{ id }}
          className="rounded border border-gray-300 px-4 py-2 font-medium hover:bg-gray-50"
        >
          Back to project
        </Link>
      </div>

      {(statusesError || typesError) && (
        <ErrorBanner>Error loading statuses and types</ErrorBanner>
      )}
      {message && <ErrorBanner>{message}</ErrorBanner>}
      {doneCount === 0 && statuses.length > 0 && (
        <ErrorBanner>
          No status is in the Done category, so finished work items can't be
          counted on boards or reports.
        </ErrorBanner>
      )}

      {confirming && (
        <ConfirmChange
          title={
            confirming.kind === "rename"
              ? `Rename status “${confirming.status.name}”?`
              : `Change the category of “${confirming.status.name}”?`
          }
          lines={confirming.lines}
          busy={false}
          onConfirm={() =>
            applyStatusChange(
              confirming.status.id,
              confirming.kind === "rename"
                ? { name: confirming.newName }
                : { category: confirming.newCategory },
            )
          }
          onCancel={() => setConfirming(null)}
        />
      )}

      {pending && (
        <ReplacementDialog
          kind={pending.kind}
          name={pending.item.name}
          count={pending.count}
          options={
            pending.kind === "status"
              ? statuses
                  .filter((s) => s.id !== pending.item.id)
                  .map((s) => ({ id: s.id, name: s.name }))
              : types
                  .filter(
                    (t) =>
                      t.id !== pending.item.id &&
                      t.level === (pending.item as WorkItemType).level,
                  )
                  .map((t) => ({ id: t.id, name: t.name }))
          }
          busy={deleteItem.isPending}
          error={dialogError}
          onConfirm={confirmReplacement}
          onCancel={() => {
            setPending(null);
            setDialogError(null);
          }}
        />
      )}

      {isLoading ? (
        <Loading />
      ) : (
        <>
          <StatusSection
            projectId={id}
            statuses={statuses}
            busy={deleteItem.isPending}
            onRun={runAction}
            onDelete={(item) => requestDelete("status", item.id)}
            onRename={(status, name) => {
              prepareRename(status, name).catch((err: Error) =>
                setMessage(err.message),
              );
            }}
            onCategoryChange={(status, next) => {
              prepareCategory(status, next).catch((err: Error) =>
                setMessage(err.message),
              );
            }}
          />
          <TypeSection
            projectId={id}
            types={types}
            busy={deleteItem.isPending}
            onRun={runAction}
            onDelete={(item) => requestDelete("type", item.id)}
          />
          <TransitionSection
            projectId={id}
            statuses={statuses}
            transitions={transitions}
            busy={deleteItem.isPending}
            onRun={runAction}
          />
        </>
      )}
    </div>
  );
}
