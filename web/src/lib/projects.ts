import { useQuery } from "@tanstack/react-query";
import { apiFetch, apiJson, jsonBody, type Paginated } from "./api";

export interface Project {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  modified_at: string;
}

export type PaginatedProjects = Paginated<Project>;

export interface ProjectCreate {
  name: string;
  description?: string;
  template?: string;
}

export interface ProjectUpdate {
  name?: string;
  description?: string | null;
}

export const PROJECT_LIMIT = 10;
const PROJECT_OPTIONS_LIMIT = 100;

export function fetchProjects(
  limit: number,
  offset: number,
  search?: string,
): Promise<PaginatedProjects> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  if (search) params.set("search", search);
  return apiJson(`/api/v1/projects/?${params}`, "Failed to fetch projects");
}

export function fetchProject(id: string): Promise<Project> {
  return apiJson(`/api/v1/projects/${id}`, "Failed to fetch project");
}

export function createProject(item: ProjectCreate): Promise<Project> {
  return apiJson(
    "/api/v1/projects/",
    "Failed to create project",
    jsonBody("POST", item),
  );
}

export function updateProject(
  id: string,
  item: ProjectUpdate,
): Promise<Project> {
  return apiJson(
    `/api/v1/projects/${id}`,
    "Failed to update project",
    jsonBody("PATCH", item),
  );
}

// The API explains 409 responses in `detail` (project still has work items or boards)
export async function deleteProject(id: string): Promise<void> {
  await apiFetch(`/api/v1/projects/${id}`, "Failed to delete project", {
    method: "DELETE",
  });
}

// Projects for select boxes; shared by every page that needs a project picker
export function useProjectOptions() {
  return useQuery({
    queryKey: ["projects", "options"],
    queryFn: () => fetchProjects(PROJECT_OPTIONS_LIMIT, 0),
  });
}
