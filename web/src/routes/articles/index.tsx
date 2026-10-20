import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { ARTICLE_LIMIT, fetchArticles } from "../../lib/articles";
import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { ErrorBanner } from "../../components/shared/ErrorBanner";
import { Loading } from "../../components/shared/Loading";
import { Pagination } from "../../components/shared/Pagination";

export const Route = createFileRoute("/articles/")({
  component: ArticlesPage,
});

function ArticlesPage() {
  useBreadcrumbs([{ label: "Knowledge base" }]);
  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState("");

  const { data, isLoading, error } = useQuery({
    queryKey: ["articles", offset, search],
    queryFn: () => fetchArticles(ARTICLE_LIMIT, offset, search.trim()),
  });

  const items = data?.results ?? [];
  const total = data?.total ?? 0;

  return (
    <div className="space-y-4 p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
        <h1 className="text-2xl font-bold">Knowledge base</h1>
        <Link
          to="/articles/create"
          className="rounded bg-blue-600 px-4 py-2 text-center font-medium text-white hover:bg-blue-700"
        >
          New article
        </Link>
      </div>

      <input
        type="search"
        aria-label="Search articles"
        placeholder="Search articles"
        value={search}
        onChange={(e) => {
          setSearch(e.target.value);
          setOffset(0);
        }}
        className="w-full rounded border border-gray-300 px-3 py-2"
      />

      {error && <ErrorBanner>Error loading articles</ErrorBanner>}

      {isLoading ? (
        <Loading />
      ) : items.length === 0 ? (
        <div className="text-center text-gray-500">
          {search.trim() ? "No articles match this search" : "No articles yet"}
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {items.map((article) => (
            <Link
              key={article.id}
              to="/articles/$id"
              params={{ id: article.id }}
              className="flex flex-col gap-1 rounded border border-gray-200 p-4 hover:border-blue-400 hover:bg-blue-50 transition"
            >
              <h2 className="font-semibold text-blue-600">{article.title}</h2>
              {article.labels.length > 0 && (
                <span className="text-xs text-gray-600">
                  {article.labels.join(", ")}
                </span>
              )}
            </Link>
          ))}
        </div>
      )}

      <Pagination
        offset={offset}
        limit={ARTICLE_LIMIT}
        total={total}
        disabled={isLoading}
        onChange={setOffset}
      />
    </div>
  );
}
