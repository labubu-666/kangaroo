import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useId, useState } from "react";
import { DragDropProvider, useDroppable } from "@dnd-kit/react";
import type { DragEndEvent } from "@dnd-kit/react";
import type { BoardView } from "../../lib/boards";
import { deleteBoard, fetchBoard, fetchBoardView } from "../../lib/boards";
import { fetchProject } from "../../lib/projects";
import { updateWorkItem, type WorkItem } from "../../lib/work-items";
import type { ProjectStatus } from "../../lib/workflow";
import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { removeRecent, useRecordRecent } from "../../lib/recent";
import { useDismiss } from "../../lib/use-dismiss";
import { useDocumentTitle } from "../../lib/use-document-title";
import { BoardCard } from "../../components/boards/BoardCard";
import { DoneStatusWarning } from "../../components/workflow/DoneStatusWarning";
import { lacksDoneStatus } from "../../lib/done-status";
import { FilterPreview } from "../../components/boards/FilterPreview";

import { ErrorBanner } from "../../components/shared/ErrorBanner";
import { Loading } from "../../components/shared/Loading";

export const Route = createFileRoute("/projects/$id_/boards/$boardId")({
  component: BoardDetail,
});

function BoardDetail() {
  const { id, boardId } = Route.useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const viewKey = ["boards", boardId, "view"];
  const [menuOpen, setMenuOpen] = useState(false);
  const menuId = useId();
  const menuRef = useDismiss<HTMLDivElement>(menuOpen, () =>
    setMenuOpen(false),
  );

  const {
    data: board,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["boards", boardId],
    queryFn: () => fetchBoard(boardId),
  });

  const { data: project } = useQuery({
    queryKey: ["projects", id],
    queryFn: () => fetchProject(id),
  });

  const { data: view, error: viewError } = useQuery({
    queryKey: viewKey,
    queryFn: () => fetchBoardView(boardId),
  });

  const moveMutation = useMutation({
    mutationFn: ({ itemId, statusId }: { itemId: string; statusId: string }) =>
      updateWorkItem(itemId, { status_id: statusId }),
    // Move the card immediately so the drop feels instant; roll back if the server rejects it
    onMutate: async ({ itemId, statusId }) => {
      await queryClient.cancelQueries({ queryKey: viewKey });
      const previous = queryClient.getQueryData<BoardView>(viewKey);
      if (previous) {
        queryClient.setQueryData<BoardView>(
          viewKey,
          moveItem(previous, itemId, statusId),
        );
      }
      return { previous };
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(viewKey, context.previous);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: viewKey });
      queryClient.invalidateQueries({ queryKey: ["work-items"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteBoard(boardId),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: ["boards", boardId] });
      removeRecent("board", boardId);
      queryClient.invalidateQueries({ queryKey: ["boards"] });
      navigate({ to: "/projects/$id", params: { id } });
    },
  });

  const handleDelete = () => {
    setMenuOpen(false);
    if (confirm("Are you sure you want to delete this board?")) {
      deleteMutation.mutate();
    }
  };

  useBreadcrumbs([
    { label: "Projects", to: "/projects" },
    {
      label: project?.name ?? "Loading...",
      to: "/projects/$id",
      params: { id },
    },
    {
      label: "Boards",
      to: "/boards",
      search: { filter: `project.id == '${id}'` },
    },
    { label: board?.name ?? "Loading..." },
  ]);
  useDocumentTitle(board?.name);

  useRecordRecent(
    board &&
      project && {
        type: "board",
        id: board.id,
        title: board.name,
        parent: project.name,
        to: "/projects/$id/boards/$boardId",
        params: { id, boardId: board.id },
      },
  );

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

  return (
    <div className="space-y-6 p-4">
      {error && <ErrorBanner>Error loading board</ErrorBanner>}

      {viewError && <ErrorBanner>Error loading board items</ErrorBanner>}

      {view && lacksDoneStatus(view.columns.map((c) => c.status.category)) && (
        <DoneStatusWarning />
      )}

      {moveMutation.error && (
        <ErrorBanner>{moveMutation.error.message}</ErrorBanner>
      )}

      {deleteMutation.error && (
        <ErrorBanner>{deleteMutation.error.message}</ErrorBanner>
      )}

      {isLoading ? (
        <Loading />
      ) : board ? (
        <>
          <div className="flex flex-wrap items-start justify-between gap-4">
            <h1 className="min-w-0 break-words text-2xl font-bold sm:text-3xl">
              {board.name}
            </h1>
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
                  aria-label="Board actions"
                  className="absolute right-0 z-10 mt-2 flex min-w-32 flex-col rounded border border-border bg-surface py-1 shadow-lg"
                >
                  <Link
                    to="/projects/$id/boards/$boardId/edit"
                    params={{ id, boardId: board.id }}
                    role="menuitem"
                    onClick={() => setMenuOpen(false)}
                    className="px-3 py-2 font-medium hover:bg-surface-strong"
                  >
                    Edit
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

          {board.filter && <FilterPreview filter={board.filter} />}

          <DragDropProvider onDragEnd={handleDragEnd}>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              {(view?.columns ?? []).map(({ status, items }) => (
                <BoardColumnView
                  key={status.id}
                  status={status}
                  items={items}
                />
              ))}
            </div>
          </DragDropProvider>
        </>
      ) : null}
    </div>
  );
}

function BoardColumnView({
  status,
  items,
}: {
  status: ProjectStatus;
  items: WorkItem[];
}) {
  const { ref, isDropTarget } = useDroppable({ id: status.id });

  return (
    <section
      ref={ref}
      className={`flex min-h-64 min-w-0 flex-col gap-3 rounded border p-3 transition-colors ${
        isDropTarget
          ? "border-blue-400 dark:border-blue-500 bg-primary-subtle"
          : "border-border bg-surface-muted"
      }`}
    >
      <h2 className="flex items-center justify-between font-semibold">
        {status.name}
        <span className="text-sm text-fg-muted">{items.length}</span>
      </h2>

      {items.length === 0 ? (
        <p className="text-center text-sm text-fg-muted">No items</p>
      ) : (
        items.map((item) => <BoardCard key={item.id} item={item} />)
      )}
    </section>
  );
}

// Returns a copy of the view with the item moved into the column for `status`
function moveItem(
  view: BoardView,
  itemId: string,
  statusId: string,
): BoardView {
  const moved = view.columns
    .flatMap((column) => column.items)
    .find((item) => item.id === itemId);
  if (!moved) return view;

  return {
    ...view,
    columns: view.columns.map((column) => {
      const remaining = column.items.filter((item) => item.id !== itemId);
      return column.status.id === statusId
        ? {
            ...column,
            items: [
              ...remaining,
              { ...moved, status_id: statusId, status: column.status },
            ],
          }
        : { ...column, items: remaining };
    }),
  };
}
