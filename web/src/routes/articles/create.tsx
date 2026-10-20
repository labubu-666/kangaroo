import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createArticle } from "../../lib/articles";
import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { ArticleForm } from "../../components/articles/ArticleForm";

export const Route = createFileRoute("/articles/create")({
  component: CreateArticle,
});

function CreateArticle() {
  useBreadcrumbs([
    { label: "Knowledge base", to: "/articles" },
    { label: "New" },
  ]);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (values: { title: string; body: string; labels: string[] }) =>
      createArticle({
        title: values.title.trim(),
        body: values.body,
        labels: values.labels,
      }),
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey: ["articles"] });
      navigate({ to: "/articles/$id", params: { id: created.id } });
    },
  });

  return (
    <div className="space-y-4 p-4">
      <h1 className="text-2xl font-bold">Create article</h1>
      <ArticleForm
        initial={{ title: "", body: "", labels: [] }}
        submitLabel="Create"
        pendingLabel="Creating..."
        cancelTo="/articles"
        disabled={mutation.isPending}
        error={mutation.error?.message ?? null}
        onSubmit={(values) => mutation.mutate(values)}
      />
    </div>
  );
}
