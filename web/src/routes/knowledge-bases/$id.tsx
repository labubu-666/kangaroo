import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useId, useState } from "react";
import {
  ARTICLE_DEFAULT_SORT,
  ARTICLE_LIMIT,
  ARTICLE_SORTS,
  fetchArticles,
} from "../../lib/articles";
import {
  deleteKnowledgeBase,
  fetchKnowledgeBase,
  updateKnowledgeBase,
} from "../../lib/knowledge-bases";
import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { ErrorBanner } from "../../components/shared/ErrorBanner";
import { InlineEdit } from "../../components/InlineEdit";
import { Loading } from "../../components/shared/Loading";
import { Pagination } from "../../components/shared/Pagination";
import { useDismiss } from "../../lib/use-dismiss";

export const Route = createFileRoute("/knowledge-bases/$id")({
  component: KnowledgeBaseDetail,
  validateSearch: (search: Record<string, unknown>): { sort?: string } => ({
    sort:
      typeof search.sort === "string" && search.sort !== ""
        ? search.sort
        : undefined,
  }),
});

function KnowledgeBaseDetail() {
  const { id } = Route.useParams();
  const { sort = ARTICLE_DEFAULT_SORT } = Route.useSearch();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [offset, setOffset] = useState(0);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuId = useId();
  const menuRef = useDismiss<HTMLDivElement>(menuOpen, () =>
    setMenuOpen(false),
  );

  const {
    data: knowledgeBase,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["knowledge-bases", id],
    queryFn: () => fetchKnowledgeBase(id),
  });

  const { data: articles } = useQuery({
    queryKey: ["articles", "in", id, offset, sort],
    queryFn: () => fetchArticles(ARTICLE_LIMIT, offset, id, undefined, sort),
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteKnowledgeBase(id),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: ["knowledge-bases", id] });
      queryClient.invalidateQueries({ queryKey: ["knowledge-bases"] });
      navigate({ to: "/knowledge-bases" });
    },
  });

  const saveName = async (name: string) => {
    await updateKnowledgeBase(id, { name: name.trim() });
    queryClient.invalidateQueries({ queryKey: ["knowledge-bases"] });
  };

  const handleDelete = () => {
    setMenuOpen(false);
    if (confirm("Are you sure you want to delete this knowledge base?")) {
      deleteMutation.mutate();
    }
  };

  useBreadcrumbs([
    { label: "Knowledge bases", to: "/knowledge-bases" },
    { label: knowledgeBase?.name ?? "Loading..." },
  ]);

  if (isLoading) return <Loading />;
  if (error || !knowledgeBase) {
    return <ErrorBanner>Error loading knowledge base</ErrorBanner>;
  }

  const items = articles?.results ?? [];
  const total = articles?.total ?? 0;

  return (
    <div className="space-y-6 p-4">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <InlineEdit
            value={knowledgeBase.name}
            onSave={saveName}
            ariaLabel="name"
            placeholder="Enter knowledge base name"
            requiredMessage="Name is required"
            textClassName="text-2xl font-bold sm:text-3xl"
          >
            <h1 className="cursor-pointer break-words text-2xl font-bold sm:text-3xl">
              {knowledgeBase.name}
            </h1>
          </InlineEdit>
          {knowledgeBase.description && (
            <p className="mt-2 whitespace-pre-wrap text-gray-600">
              {knowledgeBase.description}
            </p>
          )}
          {knowledgeBase.labels.length > 0 && (
            <ul className="mt-2 flex flex-wrap gap-2">
              {knowledgeBase.labels.map((label) => (
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
        <div ref={menuRef} className="relative">
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
              aria-label="Knowledge base actions"
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

      {deleteMutation.error && (
        <ErrorBanner>{deleteMutation.error.message}</ErrorBanner>
      )}

      <div className="space-y-4">
        <div className="flex flex-wrap justify-between gap-4">
          <h2 className="text-xl font-semibold">Articles</h2>
          <div className="flex items-center gap-2">
            <select
              aria-label="Sort articles"
              value={sort}
              onChange={(e) => {
                setOffset(0);
                navigate({
                  to: "/knowledge-bases/$id",
                  params: { id },
                  search: { sort: e.target.value },
                });
              }}
              className="rounded border border-gray-300 px-3 py-2"
            >
              {ARTICLE_SORTS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <Link
              to="/knowledge-bases/$id/articles/create"
              params={{ id }}
              className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
            >
              New article
            </Link>
          </div>
        </div>

        {items.length === 0 ? (
          <div className="text-center text-gray-500">No articles yet</div>
        ) : (
          <div className="flex flex-col gap-4">
            {items.map((article) => (
              <Link
                key={article.id}
                to="/articles/$id"
                params={{ id: article.id }}
                className="flex flex-col gap-1 rounded border border-gray-200 p-4 hover:border-blue-400 hover:bg-blue-50 transition"
              >
                <h3 className="font-semibold text-blue-600">{article.title}</h3>
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
          disabled={false}
          onChange={setOffset}
        />
      </div>
    </div>
  );
}
