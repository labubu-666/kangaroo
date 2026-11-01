import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { useBreadcrumbs } from "../components/breadcrumbs/BreadcrumbsContext";
import { CopyBase } from "../components/shared/CopyBase";
import { ErrorBanner } from "../components/shared/ErrorBanner";
import { Loading } from "../components/shared/Loading";
import {
  createApiKey,
  fetchApiKeys,
  revokeApiKey,
  type ApiKeyCreated,
} from "../lib/api-keys";

export const Route = createFileRoute("/api-keys")({
  component: ApiKeysPage,
});

function ApiKeysPage() {
  useBreadcrumbs([{ label: "API keys" }]);
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [nameError, setNameError] = useState<string | null>(null);
  const [created, setCreated] = useState<ApiKeyCreated | null>(null);

  const {
    data: keys,
    error,
    isLoading,
  } = useQuery({
    queryKey: ["api-keys"],
    queryFn: fetchApiKeys,
  });

  const refresh = () =>
    queryClient.invalidateQueries({ queryKey: ["api-keys"] });

  const createMutation = useMutation({
    mutationFn: createApiKey,
    onSuccess: (key) => {
      setCreated(key);
      setName("");
      refresh();
    },
  });

  const revokeMutation = useMutation({
    mutationFn: revokeApiKey,
    onSuccess: () => {
      setCreated(null);
      refresh();
    },
  });

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!name.trim()) {
      setNameError("Name is required");
      return;
    }
    setNameError(null);
    createMutation.mutate({ name: name.trim() });
  };

  const revoke = (id: string) => {
    if (!confirm("Revoke this API key? Anything using it will stop working."))
      return;
    revokeMutation.mutate(id);
  };

  return (
    <div className="space-y-6 p-4 sm:p-8">
      <h1 className="text-2xl font-bold">API keys</h1>
      <p className="text-fg-secondary">
        An API key lets a script or service call the API as you. Send it as{" "}
        <code>Authorization: Bearer &lt;key&gt;</code>. The key is shown only
        once, so copy it when it is created.
      </p>

      {createMutation.error && (
        <ErrorBanner>{createMutation.error.message}</ErrorBanner>
      )}
      {revokeMutation.error && (
        <ErrorBanner>{revokeMutation.error.message}</ErrorBanner>
      )}

      {created && (
        <div className="space-y-2 rounded border border-border bg-surface p-4">
          <p className="font-medium">
            Copy your new key now. You won't be able to see it again.
          </p>
          <CopyBase value={created.key} ariaLabel="Copy API key">
            <span className="break-all">{created.key}</span>
          </CopyBase>
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        autoComplete="off"
        className="space-y-4 rounded border border-border p-4"
      >
        <div className="space-y-2">
          <label htmlFor="api-key-name" className="block font-medium">
            Name *
          </label>
          <input
            id="api-key-name"
            type="text"
            placeholder="For example: nightly-import"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded border border-border-strong px-3 py-2"
          />
          {nameError && <p className="text-sm text-danger">{nameError}</p>}
        </div>
        <button
          type="submit"
          disabled={createMutation.isPending}
          className="rounded bg-primary px-4 py-2 font-medium text-on-primary hover:bg-primary-hover disabled:bg-fg-disabled"
        >
          {createMutation.isPending ? "Creating..." : "Create API key"}
        </button>
      </form>

      {isLoading && <Loading />}
      {error && <ErrorBanner>{error.message}</ErrorBanner>}
      {keys && keys.length === 0 && (
        <p className="text-fg-muted">You have no API keys.</p>
      )}
      {keys && keys.length > 0 && (
        <table className="w-full text-left text-sm">
          <thead className="border-b border-border text-fg-muted">
            <tr>
              <th className="py-2 font-medium">Name</th>
              <th className="py-2 font-medium">Created</th>
              <th className="py-2 font-medium">Last used</th>
              <th className="py-2 font-medium">Expires</th>
              <th className="py-2" />
            </tr>
          </thead>
          <tbody>
            {keys.map((key) => (
              <tr key={key.id} className="border-b border-border">
                <td className="py-2 font-medium">{key.name}</td>
                <td className="py-2">
                  {new Date(key.created_at).toLocaleString()}
                </td>
                <td className="py-2">
                  {key.last_used_at
                    ? new Date(key.last_used_at).toLocaleString()
                    : "Never"}
                </td>
                <td className="py-2">
                  {key.expires_at
                    ? new Date(key.expires_at).toLocaleString()
                    : "Never"}
                </td>
                <td className="py-2 text-right">
                  <button
                    type="button"
                    onClick={() => revoke(key.id)}
                    disabled={revokeMutation.isPending}
                    className="rounded border border-border-strong px-3 py-1 hover:bg-surface-muted"
                  >
                    Revoke
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
