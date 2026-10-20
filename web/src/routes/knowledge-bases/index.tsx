import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import {
  KNOWLEDGE_BASE_LIMIT,
  fetchKnowledgeBases,
} from "../../lib/knowledge-bases";
import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { ErrorBanner } from "../../components/shared/ErrorBanner";
import { Loading } from "../../components/shared/Loading";
import { Pagination } from "../../components/shared/Pagination";

export const Route = createFileRoute("/knowledge-bases/")({
  component: KnowledgeBasesPage,
});

function KnowledgeBasesPage() {
  useBreadcrumbs([{ label: "Knowledge bases" }]);
  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState("");

  const { data, isLoading, error } = useQuery({
    queryKey: ["knowledge-bases", offset, search],
    queryFn: () =>
      fetchKnowledgeBases(KNOWLEDGE_BASE_LIMIT, offset, search.trim()),
  });

  const items = data?.results ?? [];
  const total = data?.total ?? 0;

  return (
    <div className="space-y-4 p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
        <h1 className="text-2xl font-bold">Knowledge bases</h1>
        <Link
          to="/knowledge-bases/create"
          className="rounded bg-blue-600 px-4 py-2 text-center font-medium text-white hover:bg-blue-700"
        >
          New knowledge base
        </Link>
      </div>

      <input
        type="search"
        aria-label="Search knowledge bases"
        placeholder="Search knowledge bases"
        value={search}
        onChange={(e) => {
          setSearch(e.target.value);
          setOffset(0);
        }}
        className="w-full rounded border border-gray-300 px-3 py-2"
      />

      {error && <ErrorBanner>Error loading knowledge bases</ErrorBanner>}

      {isLoading ? (
        <Loading />
      ) : items.length === 0 ? (
        <div className="text-center text-gray-500">
          {search.trim()
            ? "No knowledge bases match this search"
            : "No knowledge bases yet"}
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {items.map((kb) => (
            <Link
              key={kb.id}
              to="/knowledge-bases/$id"
              params={{ id: kb.id }}
              className="flex flex-col gap-1 rounded border border-gray-200 p-4 hover:border-blue-400 hover:bg-blue-50 transition"
            >
              <h2 className="font-semibold text-blue-600">{kb.name}</h2>
              {kb.description && (
                <p className="text-sm text-gray-600">{kb.description}</p>
              )}
            </Link>
          ))}
        </div>
      )}

      <Pagination
        offset={offset}
        limit={KNOWLEDGE_BASE_LIMIT}
        total={total}
        disabled={isLoading}
        onChange={setOffset}
      />
    </div>
  );
}
