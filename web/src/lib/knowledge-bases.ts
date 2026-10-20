import { apiFetch, apiJson, jsonBody, type Paginated } from "./api";

export interface KnowledgeBase {
  id: string;
  name: string;
  description: string | null;
  labels: string[];
  created_at: string;
  modified_at: string;
}

export type PaginatedKnowledgeBases = Paginated<KnowledgeBase>;

export interface KnowledgeBaseInput {
  name: string;
  description: string | null;
  labels: string[];
}

export interface KnowledgeBaseUpdate {
  name?: string;
  description?: string | null;
  labels?: string[];
}

export const KNOWLEDGE_BASE_LIMIT = 10;

export function fetchKnowledgeBases(
  limit: number,
  offset: number,
  search?: string,
): Promise<PaginatedKnowledgeBases> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  if (search) params.set("search", search);
  return apiJson(
    `/api/v1/knowledge-bases/?${params}`,
    "Failed to fetch knowledge bases",
  );
}

export function fetchKnowledgeBase(id: string): Promise<KnowledgeBase> {
  return apiJson(
    `/api/v1/knowledge-bases/${id}`,
    "Failed to fetch knowledge base",
  );
}

export function updateKnowledgeBase(
  id: string,
  item: KnowledgeBaseUpdate,
): Promise<KnowledgeBase> {
  return apiJson(
    `/api/v1/knowledge-bases/${id}`,
    "Failed to update knowledge base",
    jsonBody("PATCH", item),
  );
}

export function createKnowledgeBase(
  item: KnowledgeBaseInput,
): Promise<KnowledgeBase> {
  return apiJson(
    "/api/v1/knowledge-bases/",
    "Failed to create knowledge base",
    jsonBody("POST", item),
  );
}

export function replaceKnowledgeBase(
  id: string,
  item: KnowledgeBaseInput,
): Promise<KnowledgeBase> {
  return apiJson(
    `/api/v1/knowledge-bases/${id}`,
    "Failed to save knowledge base",
    jsonBody("PUT", item),
  );
}

export async function deleteKnowledgeBase(id: string): Promise<void> {
  await apiFetch(
    `/api/v1/knowledge-bases/${id}`,
    "Failed to delete knowledge base",
    { method: "DELETE" },
  );
}
