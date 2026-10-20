import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useId, useState } from "react";
import {
  deleteArticle,
  fetchArticle,
  replaceArticle,
} from "../../lib/articles";
import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { ArticleForm } from "../../components/articles/ArticleForm";
import { ErrorBanner } from "../../components/shared/ErrorBanner";
import { Loading } from "../../components/shared/Loading";

export const Route = createFileRoute("/articles/$id")({
  component: ArticleDetail,
});

function ArticleDetail() {
  const { id } = Route.useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuId = useId();

  const {
    data: article,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["articles", id],
    queryFn: () => fetchArticle(id),
  });

  const saveMutation = useMutation({
    mutationFn: (values: { title: string; body: string; labels: string[] }) =>
      replaceArticle(id, {
        title: values.title.trim(),
        body: values.body,
        labels: values.labels,
      }),
    onSuccess: (updated) => {
      queryClient.setQueryData(["articles", id], updated);
      queryClient.invalidateQueries({ queryKey: ["articles"] });
      setEditing(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteArticle(id),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: ["articles", id] });
      queryClient.invalidateQueries({ queryKey: ["articles"] });
      navigate({ to: "/articles" });
    },
  });

  const handleDelete = () => {
    setMenuOpen(false);
    if (confirm("Are you sure you want to delete this article?")) {
      deleteMutation.mutate();
    }
  };

  useBreadcrumbs([
    { label: "Knowledge base", to: "/articles" },
    { label: article?.title ?? "Loading..." },
  ]);

  if (isLoading) return <Loading />;
  if (error || !article) {
    return <ErrorBanner>Error loading article</ErrorBanner>;
  }

  if (editing) {
    return (
      <div className="space-y-4 p-4">
        <h1 className="text-2xl font-bold">Edit article</h1>
        <ArticleForm
          initial={{
            title: article.title,
            body: article.body,
            labels: article.labels,
          }}
          submitLabel="Save"
          pendingLabel="Saving..."
          cancelTo="/articles/$id"
          cancelParams={{ id }}
          disabled={saveMutation.isPending}
          error={saveMutation.error?.message ?? null}
          onSubmit={(values) => saveMutation.mutate(values)}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-4">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <h1 className="break-words text-2xl font-bold sm:text-3xl">
            {article.title}
          </h1>
          {article.labels.length > 0 && (
            <ul className="mt-2 flex flex-wrap gap-2">
              {article.labels.map((label) => (
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
              aria-label="Article actions"
              className="absolute right-0 z-10 mt-2 flex min-w-32 flex-col rounded border border-gray-200 bg-white py-1 shadow-lg"
            >
              <button
                type="button"
                role="menuitem"
                onClick={() => {
                  setMenuOpen(false);
                  setEditing(true);
                }}
                className="px-3 py-2 text-left font-medium hover:bg-gray-100"
              >
                Edit
              </button>
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

      {/* The HTML is sanitized by the API before it reaches the page. */}
      <article
        className="max-w-none"
        dangerouslySetInnerHTML={{ __html: article.html }}
      />
    </div>
  );
}
