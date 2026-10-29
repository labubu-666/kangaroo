import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useId, useState } from "react";
import { deleteArticle, fetchArticle, updateArticle } from "../../lib/articles";
import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { fetchKnowledgeBase } from "../../lib/knowledge-bases";
import { ErrorBanner } from "../../components/shared/ErrorBanner";
import { InlineEdit } from "../../components/InlineEdit";
import { CopyId } from "../../components/shared/CopyId";
import { LabelsEditor } from "../../components/shared/LabelsEditor";
import { Loading } from "../../components/shared/Loading";
import { useDismiss } from "../../lib/use-dismiss";
import { removeRecent, useRecordRecent } from "../../lib/recent";

export const Route = createFileRoute("/articles/$id")({
  component: ArticleDetail,
});

function ArticleDetail() {
  const { id } = Route.useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuId = useId();
  const menuRef = useDismiss<HTMLDivElement>(menuOpen, () =>
    setMenuOpen(false),
  );

  const {
    data: article,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["articles", id],
    queryFn: () => fetchArticle(id),
  });

  const { data: knowledgeBase } = useQuery({
    queryKey: ["knowledge-bases", article?.knowledge_base_id],
    queryFn: () => fetchKnowledgeBase(article?.knowledge_base_id ?? ""),
    enabled: article !== undefined,
  });

  const saveTitle = async (title: string) => {
    await updateArticle(id, { title: title.trim() });
    queryClient.invalidateQueries({ queryKey: ["articles"] });
  };

  const saveBody = async (body: string) => {
    await updateArticle(id, { body });
    queryClient.invalidateQueries({ queryKey: ["articles"] });
  };

  const labelsMutation = useMutation({
    mutationFn: (labels: string[]) => updateArticle(id, { labels }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["articles"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteArticle(id),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: ["articles", id] });
      removeRecent("article", id);
      queryClient.invalidateQueries({ queryKey: ["articles"] });
      navigate({
        to: "/knowledge-bases/$id",
        params: { id: article?.knowledge_base_id ?? "" },
      });
    },
  });

  const handleDelete = () => {
    setMenuOpen(false);
    if (confirm("Are you sure you want to delete this article?")) {
      deleteMutation.mutate();
    }
  };

  useBreadcrumbs([
    {
      label: "Knowledge bases",
      to: "/knowledge-bases",
    },
    {
      label: knowledgeBase?.name ?? "Loading...",
      to: "/knowledge-bases/$id",
      params: { id: article?.knowledge_base_id ?? "" },
    },
    { label: article?.title ?? "Loading..." },
  ]);

  useRecordRecent(
    article && {
      type: "article",
      id: article.id,
      title: article.title,
      to: "/articles/$id",
      params: { id: article.id },
    },
  );

  if (isLoading) return <Loading />;
  if (error || !article) {
    return <ErrorBanner>Error loading article</ErrorBanner>;
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col space-y-6 p-4">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <InlineEdit
            value={article.title}
            onSave={saveTitle}
            ariaLabel="title"
            placeholder="Enter article title"
            requiredMessage="Title is required"
            textClassName="text-2xl font-bold sm:text-3xl"
          >
            <h1 className="cursor-pointer break-words text-2xl font-bold sm:text-3xl">
              {article.title}
            </h1>
          </InlineEdit>
        </div>
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
              aria-label="Article actions"
              className="absolute right-0 z-10 mt-2 flex min-w-32 flex-col rounded border border-border bg-surface py-1 shadow-lg"
            >
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

      {deleteMutation.error && (
        <ErrorBanner>{deleteMutation.error.message}</ErrorBanner>
      )}

      <div className="grid flex-1 grid-cols-1 gap-6 md:grid-cols-3">
        <div className="flex min-h-0 min-w-0 flex-1 flex-col rounded border border-border p-4 sm:p-6 md:col-span-2">
          {/* The HTML is sanitized by the API before it reaches the page. */}
          <InlineEdit
            value={article.body}
            onSave={saveBody}
            ariaLabel="body"
            placeholder="Write the article in Markdown"
            requiredMessage="Body is required"
            language="markdown"
            fill
          >
            {article.body ? (
              <article
                className="prose dark:prose-invert max-w-none"
                dangerouslySetInnerHTML={{ __html: article.html }}
              />
            ) : (
              <p className="text-sm text-fg-muted">No body yet</p>
            )}
          </InlineEdit>
        </div>

        <aside className="space-y-5 rounded border border-border p-4 sm:p-6 md:col-span-1">
          <LabelsEditor
            labels={article.labels}
            onChange={(labels) => labelsMutation.mutate(labels)}
            disabled={labelsMutation.isPending}
          />

          <div>
            <p className="text-sm font-medium text-fg-secondary">Viewed</p>
            <p className="text-sm text-fg-muted">
              {article.viewed_at
                ? new Date(article.viewed_at).toLocaleString()
                : "Never"}
            </p>
          </div>

          <div>
            <p className="text-sm font-medium text-fg-secondary">Created</p>
            <p className="text-sm text-fg-muted">
              {new Date(article.created_at).toLocaleString()}
            </p>
          </div>

          <div>
            <p className="text-sm font-medium text-fg-secondary">Modified</p>
            <p className="text-sm text-fg-muted">
              {new Date(article.modified_at).toLocaleString()}
            </p>
          </div>

          <div>
            <CopyId
              id={article.id}
              url={`${window.location.origin}/web/articles/${article.id}`}
            />
          </div>
        </aside>
      </div>
    </div>
  );
}
