import { apiJson, type Paginated } from "./api";

export interface Invocation {
  id: string;
  function_id: string;
  stdout: string;
  stderr: string;
  exit_code: number;
  created_at: string;
  modified_at: string;
}

export type PaginatedInvocations = Paginated<Invocation>;

export const INVOCATION_LIMIT = 10;

export function fetchInvocations(
  limit: number,
  offset: number,
  functionId?: string,
): Promise<PaginatedInvocations> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  if (functionId) params.set("function_id", functionId);
  return apiJson(
    `/api/v1/invocations/?${params}`,
    "Failed to fetch invocations",
  );
}

export function fetchInvocation(id: string): Promise<Invocation> {
  return apiJson(`/api/v1/invocations/${id}`, "Failed to fetch invocation");
}
