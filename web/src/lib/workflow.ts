import { apiFetch, apiJson, jsonBody } from "./api";

export type StatusCategory = "todo" | "in_progress" | "done";
export type TypeLevel = "standard" | "subtask";

export interface ProjectStatus {
  id: string;
  project_id: string;
  name: string;
  category: StatusCategory;
  position: number;
  created_at: string;
  modified_at: string;
}

export interface WorkItemType {
  id: string;
  project_id: string;
  name: string;
  level: TypeLevel;
  position: number;
  created_at: string;
  modified_at: string;
}

// A project's statuses, in position order
export function fetchStatuses(projectId: string): Promise<ProjectStatus[]> {
  return apiJson(
    `/api/v1/statuses/?project_id=${projectId}`,
    "Failed to fetch statuses",
  );
}

// A project's work item types, in position order
export function fetchWorkItemTypes(projectId: string): Promise<WorkItemType[]> {
  return apiJson(
    `/api/v1/work-item-types/?project_id=${projectId}`,
    "Failed to fetch work item types",
  );
}

export interface StatusInput {
  name: string;
  category: StatusCategory;
  position?: number;
}

export interface WorkItemTypeInput {
  name: string;
  level: TypeLevel;
  position?: number;
}

export interface StatusTransition {
  id: string;
  project_id: string;
  from_status_id: string;
  to_status_id: string;
}

export function createStatus(
  projectId: string,
  item: StatusInput,
): Promise<ProjectStatus> {
  return apiJson(
    "/api/v1/statuses/",
    "Failed to create status",
    jsonBody("POST", { ...item, project_id: projectId }),
  );
}

export function updateStatus(
  id: string,
  item: Partial<StatusInput>,
): Promise<ProjectStatus> {
  return apiJson(
    `/api/v1/statuses/${id}`,
    "Failed to update status",
    jsonBody("PATCH", item),
  );
}

// Deleting a status in use needs a replacement; without one the API returns 409
export async function deleteStatus(
  id: string,
  replacementId?: string,
): Promise<void> {
  const query = replacementId ? `?replacement_id=${replacementId}` : "";
  await apiFetch(`/api/v1/statuses/${id}${query}`, "Failed to delete status", {
    method: "DELETE",
  });
}

export function createWorkItemType(
  projectId: string,
  item: WorkItemTypeInput,
): Promise<WorkItemType> {
  return apiJson(
    "/api/v1/work-item-types/",
    "Failed to create work item type",
    jsonBody("POST", { ...item, project_id: projectId }),
  );
}

export function updateWorkItemType(
  id: string,
  item: Partial<WorkItemTypeInput>,
): Promise<WorkItemType> {
  return apiJson(
    `/api/v1/work-item-types/${id}`,
    "Failed to update work item type",
    jsonBody("PATCH", item),
  );
}

export async function deleteWorkItemType(
  id: string,
  replacementId?: string,
): Promise<void> {
  const query = replacementId ? `?replacement_id=${replacementId}` : "";
  await apiFetch(
    `/api/v1/work-item-types/${id}${query}`,
    "Failed to delete work item type",
    { method: "DELETE" },
  );
}

export function fetchTransitions(
  projectId: string,
): Promise<StatusTransition[]> {
  return apiJson(
    `/api/v1/status-transitions/?project_id=${projectId}`,
    "Failed to fetch transitions",
  );
}

export function createTransition(
  projectId: string,
  fromStatusId: string,
  toStatusId: string,
): Promise<StatusTransition> {
  return apiJson(
    "/api/v1/status-transitions/",
    "Failed to create transition",
    jsonBody("POST", {
      project_id: projectId,
      from_status_id: fromStatusId,
      to_status_id: toStatusId,
    }),
  );
}

export async function deleteTransition(id: string): Promise<void> {
  await apiFetch(
    `/api/v1/status-transitions/${id}`,
    "Failed to delete transition",
    { method: "DELETE" },
  );
}
