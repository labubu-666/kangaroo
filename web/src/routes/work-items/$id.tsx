import { createFileRoute, Link } from "@tanstack/react-router";
import { useId, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchWorkItem,
  fetchWorkItems,
  updateWorkItem,
  deleteWorkItem,
  duplicateWorkItem,
  WORK_ITEM_LIMIT,
} from "../../lib/work-items";
import { fetchStatuses } from "../../lib/workflow";
import { fetchProject, useProjectOptions } from "../../lib/projects";
import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { removeRecent, useRecordRecent } from "../../lib/recent";
import { useGoBackOr } from "../../lib/navigation";
import { projectFilter } from "../../lib/filter-bubbles";
import { useDismiss } from "../../lib/use-dismiss";

import { CopyId } from "../../components/shared/CopyId";
import { ErrorBanner } from "../../components/shared/ErrorBanner";
import { InlineEdit } from "../../components/InlineEdit";
import { LabelsEditor } from "../../components/shared/LabelsEditor";
import { Loading } from "../../components/shared/Loading";

export const Route = createFileRoute("/work-items/$id")({
  component: WorkItemDetail,
});

function WorkItemDetail() {
  const { id } = Route.useParams();
  const navigate = Route.useNavigate();
  const goBackOr = useGoBackOr();
  const queryClient = useQueryClient();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuId = useId();
  const menuRef = useDismiss<HTMLDivElement>(menuOpen, () =>
    setMenuOpen(false),
  );

  const {
    data: item,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["work-items", id],
    queryFn: () => fetchWorkItem(id),
  });

  const updateMutation = useMutation({
    mutationFn: (statusId: string) =>
      updateWorkItem(id, { status_id: statusId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["work-items", id] });
    },
  });

  const { data: projects } = useProjectOptions();

  const { data: project } = useQuery({
    queryKey: ["projects", item?.project_id],
    queryFn: () => fetchProject(item?.project_id ?? ""),
    enabled: !!item?.project_id,
  });

  // The status choices are the item's own project's statuses
  const { data: statuses } = useQuery({
    queryKey: ["statuses", item?.project_id],
    queryFn: () => fetchStatuses(item?.project_id ?? ""),
    enabled: !!item?.project_id,
  });

  const parentId =
    item?.type.level === "subtask" ? (item.parent_id ?? undefined) : undefined;
  const { data: parent } = useQuery({
    queryKey: ["work-items", parentId],
    queryFn: () => fetchWorkItem(parentId ?? ""),
    enabled: !!parentId,
  });

  const isTask = item?.type.level === "standard";
  const { data: subtasks } = useQuery({
    queryKey: ["work-items", "subtasks", id],
    queryFn: () => fetchWorkItems(WORK_ITEM_LIMIT, 0, { parentId: id }),
    enabled: isTask,
  });

  const projectMutation = useMutation({
    mutationFn: (projectId: string) =>
      updateWorkItem(id, { project_id: projectId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["work-items"] });
    },
  });

  const labelsMutation = useMutation({
    mutationFn: (labels: string[]) => updateWorkItem(id, { labels }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["work-items", id] });
    },
  });

  const saveTitle = async (title: string) => {
    await updateWorkItem(id, { title: title.trim() });
    queryClient.invalidateQueries({ queryKey: ["work-items", id] });
  };

  const saveDescription = async (description: string) => {
    await updateWorkItem(id, { description: description.trim() || null });
    queryClient.invalidateQueries({ queryKey: ["work-items", id] });
  };

  const trashMutation = useMutation({
    mutationFn: () => updateWorkItem(id, { trashed: true }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["work-items"] });
      goBackOr(() =>
        navigate({
          to: "/work-items",
          search: { filter: projectFilter(item?.project_id) },
        }),
      );
    },
  });

  const duplicateMutation = useMutation({
    mutationFn: () => duplicateWorkItem(id),
    onSuccess: (copy) => {
      queryClient.invalidateQueries({ queryKey: ["work-items"] });
      navigate({ to: "/work-items/$id", params: { id: copy.id } });
    },
  });

  const restoreMutation = useMutation({
    mutationFn: () => updateWorkItem(id, { trashed: false }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["work-items"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteWorkItem(id),
    onSuccess: () => {
      removeRecent("work-item", id);
      queryClient.invalidateQueries({ queryKey: ["work-items"] });
      goBackOr(() =>
        navigate({
          to: "/work-items",
          search: { filter: projectFilter(item?.project_id) },
        }),
      );
    },
  });

  useRecordRecent(
    item &&
      project && {
        type: "work-item",
        id: item.id,
        title: item.title,
        parent: project.name,
        to: "/work-items/$id",
        params: { id: item.id },
      },
  );

  const handleStatusChange = (newStatusId: string) => {
    updateMutation.mutate(newStatusId);
  };

  const handleTrash = () => {
    if (confirm("Move this work item to the trash?")) {
      trashMutation.mutate();
    }
  };

  const handleDelete = () => {
    if (confirm("Permanently delete this work item? This cannot be undone.")) {
      deleteMutation.mutate();
    }
  };

  useBreadcrumbs([
    { label: "Projects", to: "/projects" },
    ...(item
      ? [
          {
            label: project?.name ?? "Loading...",
            to: "/projects/$id",
            params: { id: item.project_id },
          },
        ]
      : []),
    ...(item
      ? [
          {
            label: "Work items",
            to: "/projects/$id",
            params: { id: item.project_id },
            search: { tab: "work-items" },
          },
        ]
      : []),
    ...(parent
      ? [
          {
            label: parent.title,
            to: "/work-items/$id",
            params: { id: parent.id },
          },
        ]
      : []),
    { label: item?.title ?? "Loading..." },
  ]);

  return (
    <div className="space-y-6 p-4">
      {error && <ErrorBanner>Error loading work item</ErrorBanner>}

      {isLoading ? (
        <Loading />
      ) : item ? (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          <div className="space-y-6 md:col-span-2">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="min-w-0 flex-1">
                <InlineEdit
                  value={item.title}
                  onSave={saveTitle}
                  ariaLabel="title"
                  placeholder="Enter work item title"
                  requiredMessage="Title is required"
                  textClassName="text-2xl font-bold sm:text-3xl"
                >
                  <h1 className="cursor-pointer break-words text-2xl font-bold sm:text-3xl">
                    {item.title}
                  </h1>
                </InlineEdit>
              </div>
              {!item.trashed && (
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
                      aria-label="Work item actions"
                      className="absolute right-0 z-10 mt-2 flex min-w-40 flex-col rounded border border-border bg-surface py-1 shadow-lg"
                    >
                      <button
                        type="button"
                        role="menuitem"
                        disabled={duplicateMutation.isPending}
                        onClick={() => {
                          setMenuOpen(false);
                          duplicateMutation.mutate();
                        }}
                        className="px-3 py-2 text-left font-medium hover:bg-surface-strong disabled:text-fg-disabled"
                      >
                        Duplicate
                      </button>
                      <button
                        type="button"
                        role="menuitem"
                        disabled={trashMutation.isPending}
                        onClick={() => {
                          setMenuOpen(false);
                          handleTrash();
                        }}
                        className="px-3 py-2 text-left font-medium hover:bg-surface-strong disabled:text-fg-disabled"
                      >
                        Trash
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
            {duplicateMutation.error && (
              <ErrorBanner>{duplicateMutation.error.message}</ErrorBanner>
            )}
            {trashMutation.error && (
              <ErrorBanner>{trashMutation.error.message}</ErrorBanner>
            )}

            <div className="rounded border border-border p-4 sm:p-6">
              <InlineEdit
                value={item.description ?? ""}
                onSave={saveDescription}
                ariaLabel="description"
                placeholder="Enter work item description (optional)"
                multiline
              >
                {item.description ? (
                  <div
                    className="prose dark:prose-invert prose-sm max-w-none break-words"
                    dangerouslySetInnerHTML={{
                      __html: item.rendered_description ?? "",
                    }}
                  />
                ) : (
                  <p className="text-sm text-fg-muted">No description yet</p>
                )}
              </InlineEdit>
            </div>

            {isTask && (
              <div className="space-y-2 rounded border border-border p-4 sm:p-6">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h2 className="font-semibold text-fg-secondary">Subtasks</h2>
                  <Link
                    to="/work-items/create"
                    search={{ parentId: item.id, projectId: item.project_id }}
                    className="rounded bg-primary px-3 py-1 text-sm font-medium text-on-primary hover:bg-primary-hover"
                  >
                    Add subtask
                  </Link>
                </div>
                {(subtasks?.results ?? []).length === 0 ? (
                  <p className="text-sm text-fg-muted">No subtasks yet</p>
                ) : (
                  <ul className="list-disc space-y-1 pl-5">
                    {(subtasks?.results ?? []).map((subtask) => (
                      <li key={subtask.id}>
                        <Link
                          to="/work-items/$id"
                          params={{ id: subtask.id }}
                          className="text-primary hover:underline"
                        >
                          {subtask.title}
                        </Link>{" "}
                        <span className="text-xs text-fg-muted">
                          ({subtask.status.name})
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>

          <aside className="space-y-5 rounded border border-border p-4 sm:p-6 md:col-span-1">
            <div>
              <p className="text-sm font-medium text-fg-secondary">Type</p>
              <span className="mt-1 inline-block rounded bg-surface-strong px-2 py-0.5 text-xs font-medium text-fg-secondary">
                {item.type.name}
              </span>
            </div>

            <div>
              <label className="block text-sm font-medium text-fg-secondary">
                Status
              </label>
              <select
                value={item.status_id}
                onChange={(e) => handleStatusChange(e.target.value)}
                disabled={updateMutation.isPending}
                className="mt-2 w-full rounded border border-border-strong px-3 py-2"
              >
                {(statuses ?? []).map((status) => (
                  <option key={status.id} value={status.id}>
                    {status.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-fg-secondary">
                Project
              </label>
              <select
                value={item.project_id}
                onChange={(e) => projectMutation.mutate(e.target.value)}
                disabled={projectMutation.isPending}
                className="mt-1 w-full rounded border border-border-strong px-3 py-2"
              >
                {(projects?.results ?? []).map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </div>

            <LabelsEditor
              labels={item.labels}
              onChange={(labels) => labelsMutation.mutate(labels)}
              disabled={labelsMutation.isPending}
            />

            <div>
              <p className="text-sm font-medium text-fg-secondary">Created</p>
              <p className="text-sm text-fg-muted">
                {new Date(item.created_at).toLocaleString()}
              </p>
            </div>

            <div>
              <p className="text-sm font-medium text-fg-secondary">Modified</p>
              <p className="text-sm text-fg-muted">
                {new Date(item.modified_at).toLocaleString()}
              </p>
            </div>

            <div className="space-y-2 border-t border-border pt-4">
              {item.trashed && (
                <>
                  <p className="text-sm text-fg-secondary">
                    This item is in the trash.
                  </p>
                  {restoreMutation.error && (
                    <ErrorBanner>{restoreMutation.error.message}</ErrorBanner>
                  )}
                  {deleteMutation.error && (
                    <ErrorBanner>{deleteMutation.error.message}</ErrorBanner>
                  )}
                  <button
                    onClick={() => restoreMutation.mutate()}
                    disabled={restoreMutation.isPending}
                    className="w-full rounded bg-primary px-4 py-2 font-medium text-on-primary hover:bg-primary-hover disabled:bg-fg-disabled"
                  >
                    Restore
                  </button>
                  <button
                    onClick={handleDelete}
                    disabled={deleteMutation.isPending}
                    className="w-full rounded bg-danger px-4 py-2 font-medium text-on-primary hover:bg-danger-hover disabled:bg-fg-disabled"
                  >
                    Delete permanently
                  </button>
                </>
              )}
            </div>

            <div>
              <CopyId
                id={item.id}
                url={`${window.location.origin}/web/work-items/${item.id}`}
              />
            </div>
          </aside>
        </div>
      ) : null}
    </div>
  );
}
