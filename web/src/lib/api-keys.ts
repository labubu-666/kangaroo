import { apiFetch, apiJson, jsonBody } from "./api";

export interface ApiKey {
  id: string;
  name: string;
  created_at: string;
  last_used_at: string | null;
  expires_at: string | null;
}

export interface ApiKeyCreated extends ApiKey {
  key: string;
}

export interface ApiKeyCreate {
  name: string;
  expires_at?: string;
}

export function fetchApiKeys(): Promise<ApiKey[]> {
  return apiJson("/api/v1/api-keys/", "Failed to fetch API keys");
}

export function createApiKey(item: ApiKeyCreate): Promise<ApiKeyCreated> {
  return apiJson(
    "/api/v1/api-keys/",
    "Failed to create API key",
    jsonBody("POST", item),
  );
}

export async function revokeApiKey(id: string): Promise<void> {
  await apiFetch(`/api/v1/api-keys/${id}`, "Failed to revoke API key", {
    method: "DELETE",
  });
}
