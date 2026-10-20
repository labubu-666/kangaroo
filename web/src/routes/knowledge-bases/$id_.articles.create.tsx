import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createArticle } from "../../lib/articles";
import { fetchKnowledgeBase } from "../../lib/knowledge-bases";
import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { ArticleForm } from "../../components/articles/ArticleForm";

export const Route = createFileRoute("/knowledge-bases/$id_/articles/create")({
  component: CreateArticle,
});

function CreateArticle() {
  const { id } = Route.useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: knowledgeBase } = useQuery({
    queryKey: ["knowledge-bases", id],
    queryFn: () => fetchKnowledgeBase(id),
  });

  useBreadcrumbs([
    { label: "Knowledge bases", to: "/knowledge-bases" },
    {
      label: knowledgeBase?.name ?? "Loading...",
      to: "/knowledge-bases/$id",
      params: { id },
    },
    { label: "New article" },
  ]);

  const mutation = useMutation({
    mutationFn: (values: { title: string; body: string; labels: string[] }) =>
      createArticle({
        knowledge_base_id: id,
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
        cancelTo="/knowledge-bases/$id"
        cancelParams={{ id }}
        disabled={mutation.isPending}
        error={mutation.error?.message ?? null}
        onSubmit={(values) => mutation.mutate(values)}
      />
    </div>
  );
}
