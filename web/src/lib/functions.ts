import { apiFetch, apiJson, jsonBody, type Paginated } from "./api";
import type { Invocation } from "./invocations";

export interface Function {
  id: string;
  name: string;
  description: string | null;
  code: string;
  labels: string[];
  created_at: string;
  modified_at: string;
}

export type PaginatedFunctions = Paginated<Function>;

export interface FunctionCreate {
  name: string;
  description?: string;
  code: string;
  labels?: string[];
}

export interface FunctionUpdate {
  name?: string;
  description?: string | null;
  code?: string;
  labels?: string[];
}

export const FUNCTION_LIMIT = 10;

export function fetchFunctions(
  limit: number,
  offset: number,
  search?: string,
): Promise<PaginatedFunctions> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  if (search) params.set("search", search);
  return apiJson(`/api/v1/functions/?${params}`, "Failed to fetch functions");
}

export function fetchFunction(id: string): Promise<Function> {
  return apiJson(`/api/v1/functions/${id}`, "Failed to fetch function");
}

export function createFunction(item: FunctionCreate): Promise<Function> {
  return apiJson(
    "/api/v1/functions/",
    "Failed to create function",
    jsonBody("POST", item),
  );
}

export function updateFunction(
  id: string,
  item: FunctionUpdate,
): Promise<Function> {
  return apiJson(
    `/api/v1/functions/${id}`,
    "Failed to update function",
    jsonBody("PATCH", item),
  );
}

export async function deleteFunction(id: string): Promise<void> {
  await apiFetch(`/api/v1/functions/${id}`, "Failed to delete function", {
    method: "DELETE",
  });
}

export function runFunction(id: string): Promise<Invocation> {
  return apiJson(`/api/v1/functions/${id}/run`, "Failed to run function", {
    method: "POST",
  });
}
