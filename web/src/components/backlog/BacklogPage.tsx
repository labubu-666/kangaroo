import { DragDropProvider, useDraggable, useDroppable } from "@dnd-kit/react";
import type { DragEndEvent } from "@dnd-kit/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { useId, useState } from "react";
import {
  fetchWorkItems,
  updateWorkItem,
  WORK_ITEM_LIMIT,
  type WorkItem,
} from "../../lib/work-items";
import { fetchStatuses, type ProjectStatus } from "../../lib/workflow";
import { ErrorBanner } from "../shared/ErrorBanner";
import { Loading } from "../shared/Loading";
import { TypeIcon } from "../shared/TypeIcon";

// Each status is a section. Dragging a row onto another section moves the work item
// there, and the API refuses moves that no transition allows.
export function BacklogPage({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient();
  const [moveError, setMoveError] = useState<string | null>(null);

  const { data: statuses, isLoading } = useQuery({
    queryKey: ["statuses", projectId],
    queryFn: () => fetchStatuses(projectId),
  });

  const moveMutation = useMutation({
    mutationFn: ({ itemId, statusId }: { itemId: string; statusId: string }) =>
      updateWorkItem(itemId, { status_id: statusId }),
    onMutate: () => setMoveError(null),
    onError: (err) => setMoveError(err.message),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["work-items"] });
    },
  });

  const handleDragEnd = (event: DragEndEvent) => {
    if (event.canceled) return;
    const source = event.operation.source;
    const target = event.operation.target;
    if (!source || !target) return;
    const statusId = String(target.id);
    const currentStatusId = (source.data as { status: string }).status;
    if (statusId === currentStatusId) return;
    moveMutation.mutate({ itemId: String(source.id), statusId });
  };

  if (isLoading) return <Loading />;

  return (
    <div className="space-y-4">
      {moveError && <ErrorBanner>{moveError}</ErrorBanner>}
      <DragDropProvider onDragEnd={handleDragEnd}>
        {(statuses ?? []).map((status) => (
          <BacklogSection
            key={status.id}
            projectId={projectId}
            status={status}
          />
        ))}
      </DragDropProvider>
    </div>
  );
}

function BacklogSection({
  projectId,
  status,
}: {
  projectId: string;
  status: ProjectStatus;
}) {
  const [open, setOpen] = useState(true);
  const contentId = useId();
  const { ref, isDropTarget } = useDroppable({ id: status.id });

  const { data, isLoading, error } = useQuery({
    queryKey: ["work-items", "backlog", projectId, status.id],
    queryFn: () =>
      fetchWorkItems(WORK_ITEM_LIMIT, 0, {
        projectId,
        filter: `status == '${status.id}'`,
      }),
    enabled: open,
  });

  const items = data?.results ?? [];

  return (
    <section
      ref={ref}
      className={`overflow-hidden rounded border transition-colors ${
        isDropTarget ? "border-primary" : "border-border"
      }`}
    >
      <header
        className={`flex items-center justify-between px-4 py-2 font-semibold transition-colors ${
          isDropTarget ? "bg-primary-subtle text-primary" : "bg-surface-muted"
        }`}
      >
        <button
          type="button"
          aria-expanded={open}
          aria-controls={contentId}
          onClick={() => setOpen((value) => !value)}
          className="flex items-center gap-2"
        >
          <span aria-hidden="true">{open ? "▾" : "▸"}</span>
          {status.name}
        </button>
        <span className="text-sm text-fg-muted">{data?.total ?? 0}</span>
      </header>
      {open && (
        <div id={contentId}>
          {isLoading ? (
            <Loading />
          ) : error ? (
            <ErrorBanner>{error.message}</ErrorBanner>
          ) : items.length === 0 ? (
            <p className="p-4 text-center text-sm text-fg-muted">No items</p>
          ) : (
            <ul className="divide-y divide-border">
              {items.map((item) => (
                <BacklogRow key={item.id} item={item} />
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}

function BacklogRow({ item }: { item: WorkItem }) {
  const { ref, isDragging } = useDraggable({
    id: item.id,
    data: { status: item.status_id },
  });

  return (
    <li>
      <Link
        ref={ref}
        to="/work-items/$id"
        params={{ id: item.id }}
        className={`flex items-center gap-3 px-4 py-2 hover:bg-surface-muted ${
          isDragging ? "opacity-50" : ""
        }`}
      >
        <TypeIcon type={item.type} />
        <span className="min-w-0 flex-1 truncate font-medium text-fg">
          {item.summary}
        </span>
        {item.labels.map((label) => (
          <span
            key={label}
            className="rounded bg-surface-strong px-2 py-0.5 text-xs font-medium text-fg-secondary"
          >
            {label}
          </span>
        ))}
      </Link>
    </li>
  );
}
