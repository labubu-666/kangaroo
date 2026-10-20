import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { createKnowledgeBase } from "../../lib/knowledge-bases";
import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { ErrorBanner } from "../../components/shared/ErrorBanner";
import { LabelsEditor } from "../../components/shared/LabelsEditor";

export const Route = createFileRoute("/knowledge-bases/create")({
  component: CreateKnowledgeBase,
});

function CreateKnowledgeBase() {
  useBreadcrumbs([
    { label: "Knowledge bases", to: "/knowledge-bases" },
    { label: "New" },
  ]);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [labels, setLabels] = useState<string[]>([]);
  const [nameError, setNameError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () =>
      createKnowledgeBase({
        name: name.trim(),
        description: description.trim() || null,
        labels,
      }),
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey: ["knowledge-bases"] });
      navigate({ to: "/knowledge-bases/$id", params: { id: created.id } });
    },
  });

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setNameError(name.trim() ? null : "Name is required");
    if (!name.trim()) return;
    mutation.mutate();
  };

  return (
    <div className="space-y-4 p-4">
      <h1 className="text-2xl font-bold">Create knowledge base</h1>

      {mutation.error && <ErrorBanner>{mutation.error.message}</ErrorBanner>}

      <form
        onSubmit={handleSubmit}
        autoComplete="off"
        className="space-y-4 rounded border border-gray-200 p-4"
      >
        <div className="space-y-2">
          <label htmlFor="name" className="block font-medium">
            Name *
          </label>
          <input
            id="name"
            type="text"
            disabled={mutation.isPending}
            placeholder="Enter knowledge base name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded border border-gray-300 px-3 py-2"
          />
          {nameError && <p className="text-sm text-red-600">{nameError}</p>}
        </div>

        <div className="space-y-2">
          <label htmlFor="description" className="block font-medium">
            Description
          </label>
          <textarea
            id="description"
            disabled={mutation.isPending}
            placeholder="Enter knowledge base description (optional)"
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full rounded border border-gray-300 px-3 py-2"
          />
        </div>

        <LabelsEditor
          labels={labels}
          disabled={mutation.isPending}
          onChange={setLabels}
        />

        <div className="flex flex-wrap gap-3">
          <button
            type="submit"
            disabled={mutation.isPending}
            className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:bg-gray-400"
          >
            {mutation.isPending ? "Creating..." : "Create"}
          </button>
          <Link
            to="/knowledge-bases"
            className="rounded border border-gray-300 px-4 py-2 font-medium hover:bg-gray-50"
          >
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}
