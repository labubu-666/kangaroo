import { apiFetch, apiJson, jsonBody, type Paginated } from "./api";
import type { StatusCategory, TypeLevel } from "./workflow";

// A work item's status and type, as the API embeds them
export interface StatusRef {
  id: string;
  name: string;
  category: StatusCategory;
}

export interface TypeRef {
  id: string;
  name: string;
  level: TypeLevel;
}

export interface WorkItem {
  id: string;
  title: string;
  description: string | null;
  rendered_description: string | null;
  project_id: string;
  status_id: string;
  type_id: string;
  status: StatusRef;
  type: TypeRef;
  parent_id: string | null;
  labels: string[];
  trashed: boolean;
  created_at: string;
  modified_at: string;
}

export type PaginatedWorkItems = Paginated<WorkItem>;

export interface WorkItemCreate {
  title: string;
  description?: string;
  project_id: string;
  type_id: string;
  status_id?: string;
  parent_id?: string;
  labels?: string[];
}

export interface WorkItemUpdate {
  title?: string;
  description?: string | null;
  labels?: string[];
  status_id?: string;
  type_id?: string;
  project_id?: string;
  trashed?: boolean;
}
export const WORK_ITEM_LIMIT = 10;

export interface WorkItemFilters {
  projectId?: string;
  parentId?: string;
  search?: string;
  trashed?: boolean | "all";
  filter?: string;
}

// Live items by default; trashed=true selects only trashed items;
// trashed="all" applies no trashed condition at all.
function trashFilter(
  trashed: boolean | "all" | undefined,
  filter: string | undefined,
): string | undefined {
  if (trashed === "all") return filter;
  const state = trashed ? "trashed == true" : "trashed == false";
  return filter ? `(${filter}) and ${state}` : state;
}

export function fetchWorkItems(
  limit: number,
  offset: number,
  filters: WorkItemFilters = {},
): Promise<PaginatedWorkItems> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  if (filters.projectId) params.set("project_id", filters.projectId);
  if (filters.parentId) params.set("parent_id", filters.parentId);
  if (filters.search) params.set("search", filters.search);
  const filter = trashFilter(filters.trashed, filters.filter);
  if (filter) params.set("filter", filter);
  return apiJson(`/api/v1/work-items/?${params}`, "Failed to fetch work items");
}

export function fetchWorkItem(id: string): Promise<WorkItem> {
  return apiJson(`/api/v1/work-items/${id}`, "Failed to fetch work item");
}

export function createWorkItem(item: WorkItemCreate): Promise<WorkItem> {
  return apiJson(
    "/api/v1/work-items/",
    "Failed to create work item",
    jsonBody("POST", item),
  );
}

export function updateWorkItem(
  id: string,
  item: WorkItemUpdate,
): Promise<WorkItem> {
  return apiJson(
    `/api/v1/work-items/${id}`,
    "Failed to update work item",
    jsonBody("PATCH", item),
  );
}

export async function deleteWorkItem(id: string): Promise<void> {
  await apiFetch(`/api/v1/work-items/${id}`, "Failed to delete work item", {
    method: "DELETE",
  });
}

export function duplicateWorkItem(id: string): Promise<WorkItem> {
  return apiJson(
    `/api/v1/work-items/${id}/duplicate`,
    "Failed to duplicate work item",
    { method: "POST" },
  );
}

export type BulkDeleteRequest =
  | { ids: string[] }
  | { all_matching: true; filter?: string };

export function bulkDeleteWorkItems(
  request: BulkDeleteRequest,
): Promise<{ deleted: number }> {
  return apiJson(
    "/api/v1/work-items/bulk-delete",
    "Failed to delete work items",
    jsonBody("POST", request),
  );
}
