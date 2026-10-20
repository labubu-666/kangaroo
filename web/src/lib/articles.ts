import { apiFetch, apiJson, jsonBody, type Paginated } from "./api";

export interface Article {
  id: string;
  knowledge_base_id: string;
  title: string;
  body: string;
  labels: string[];
  created_at: string;
  modified_at: string;
}

export interface ArticleDetail extends Article {
  html: string;
}

export type PaginatedArticles = Paginated<Article>;

export interface ArticleInput {
  knowledge_base_id: string;
  title: string;
  body: string;
  labels: string[];
}

export const ARTICLE_LIMIT = 10;

export function fetchArticles(
  limit: number,
  offset: number,
  knowledgeBaseId: string,
  search?: string,
): Promise<PaginatedArticles> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
    knowledge_base_id: knowledgeBaseId,
  });
  if (search) params.set("search", search);
  return apiJson(`/api/v1/articles/?${params}`, "Failed to fetch articles");
}

export function fetchArticle(id: string): Promise<ArticleDetail> {
  return apiJson(`/api/v1/articles/${id}`, "Failed to fetch article");
}

export function createArticle(item: ArticleInput): Promise<Article> {
  return apiJson(
    "/api/v1/articles/",
    "Failed to create article",
    jsonBody("POST", item),
  );
}

export function replaceArticle(
  id: string,
  item: ArticleInput,
): Promise<Article> {
  return apiJson(
    `/api/v1/articles/${id}`,
    "Failed to save article",
    jsonBody("PUT", item),
  );
}

export async function deleteArticle(id: string): Promise<void> {
  await apiFetch(`/api/v1/articles/${id}`, "Failed to delete article", {
    method: "DELETE",
  });
}
