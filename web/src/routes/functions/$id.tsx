import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useBlocker } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useId, useState } from "react";
import {
  deleteFunction,
  fetchFunction,
  runFunction,
  updateFunction,
} from "../../lib/functions";
import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { CodeEditor } from "../../components/functions/CodeEditor";
import { InlineEdit } from "../../components/InlineEdit";
import { ConfirmChange } from "../../components/workflow/ConfirmChange";
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

  const saveFunction = async (update: { name?: string; code?: string }) => {
    const updated = await updateFunction(id, update);
    queryClient.setQueryData(["functions", id], updated);
    queryClient.invalidateQueries({ queryKey: ["functions"] });
  };

  // Null means the code has no unsaved changes; the saved code is shown as-is.
  const [draftCode, setDraftCode] = useState<string | null>(null);

  const codeMutation = useMutation({
    mutationFn: () => saveFunction({ code: draftCode ?? undefined }),
    onSuccess: () => setDraftCode(null),
  });

  const [menuOpen, setMenuOpen] = useState(false);
  const menuId = useId();

  const handleDelete = () => {
    setMenuOpen(false);
    if (confirm("Are you sure you want to delete this function?")) {
      deleteMutation.mutate();
    }
  };

  useBreadcrumbs([
    { label: "Functions", to: "/functions" },
    { label: fn?.name ?? "Loading..." },
  ]);

  const code = draftCode ?? fn?.code ?? "";
  const isModified =
    fn !== undefined && draftCode !== null && draftCode !== fn.code;
  // Delete navigates away on purpose, so it must not trigger the warning.
  const blocker = useBlocker({
    shouldBlockFn: () => isModified,
    disabled: !isModified || deleteMutation.isPending,
    withResolver: true,
  });

  const codeError =
    draftCode !== null && !draftCode.trim() ? "Code is required" : null;

  return (
    <div className="flex min-h-0 flex-1 flex-col space-y-6 p-4">
      {error && <ErrorBanner>Error loading function</ErrorBanner>}

      {blocker.status === "blocked" && (
        <ConfirmChange
          title="Discard unsaved changes?"
          lines={["Your changes to this function have not been saved."]}
          busy={false}
          onConfirm={blocker.proceed}
          onCancel={blocker.reset}
        />
      )}

      {isLoading ? (
        <Loading />
      ) : fn ? (
        <div className="flex min-h-0 flex-1 flex-col space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              <InlineEdit
                value={fn.name}
                onSave={(name) => saveFunction({ name: name.trim() })}
                ariaLabel="name"
                placeholder="Enter function name"
                requiredMessage="Name is required"
                textClassName="h-10 text-2xl font-bold sm:text-3xl"
              >
                <h1 className="flex h-10 cursor-pointer items-center break-words text-2xl font-bold sm:text-3xl">
                  {fn.name}
                </h1>
              </InlineEdit>
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
            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={() => runMutation.mutate()}
                disabled={runMutation.isPending}
                className="flex h-10 items-center gap-2 rounded bg-green-600 px-4 font-medium text-white hover:bg-green-700 disabled:bg-gray-400"
              >
                <svg
                  aria-hidden="true"
                  viewBox="0 0 24 24"
                  className="h-4 w-4 fill-current"
                >
                  <path d="M8 5v14l11-7z" />
                </svg>
                {runMutation.isPending ? "Running..." : "Run"}
              </button>
              <div className="relative">
                <button
                  type="button"
                  aria-label="More actions"
                  aria-haspopup="menu"
                  aria-expanded={menuOpen}
                  aria-controls={menuId}
                  onClick={() => setMenuOpen((open) => !open)}
                  className="flex h-10 items-center rounded border border-gray-300 px-4 font-medium hover:bg-gray-50"
                >
                  ⋯
                </button>
                {menuOpen && (
                  <div
                    id={menuId}
                    role="menu"
                    aria-label="Function actions"
                    className="absolute right-0 z-10 mt-2 flex min-w-32 flex-col rounded border border-gray-200 bg-white py-1 shadow-lg"
                  >
                    <button
                      type="button"
                      role="menuitem"
                      onClick={handleDelete}
                      disabled={deleteMutation.isPending}
                      className="px-3 py-2 text-left font-medium text-red-600 hover:bg-gray-100 disabled:text-gray-400"
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
          {deleteMutation.error && (
            <ErrorBanner>{deleteMutation.error.message}</ErrorBanner>
          )}
          {codeMutation.error && (
            <ErrorBanner>{codeMutation.error.message}</ErrorBanner>
          )}
          {codeError && <p className="text-sm text-red-600">{codeError}</p>}

          <div className="flex min-h-0 flex-1 flex-col">
            <CodeEditor
              value={code}
              ariaLabel="Code"
              readOnly={codeMutation.isPending}
              onChange={setDraftCode}
              fill
            />
          </div>

          {isModified && (
            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={() => codeMutation.mutate()}
                disabled={codeMutation.isPending || codeError !== null}
                className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:bg-gray-400"
              >
                {codeMutation.isPending ? "Saving..." : "Save"}
              </button>
              <button
                onClick={() => setDraftCode(null)}
                disabled={codeMutation.isPending}
                className="rounded border border-gray-300 px-4 py-2 font-medium hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400"
              >
                Discard
              </button>
              <span className="rounded bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
                Modified
              </span>
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}
