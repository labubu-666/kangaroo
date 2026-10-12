import { apiFetch, apiJson, jsonBody, type Paginated } from "./api";
import type { ProjectStatus } from "./workflow";
import type { WorkItem } from "./work-items";

export interface Board {
  id: string;
  name: string;
  description: string | null;
  project_id: string;
  filter: string | null;
  created_at: string;
  modified_at: string;
}

export type PaginatedBoards = Paginated<Board>;

export interface BoardCreate {
  name: string;
  description?: string;
  project_id: string;
  filter?: string;
}

export interface BoardUpdate {
  name?: string;
  description?: string | null;
  project_id?: string;
  filter?: string | null;
}

export interface BoardColumn {
  status: ProjectStatus;
  items: WorkItem[];
}

export interface BoardView {
  board: Board;
  columns: BoardColumn[];
}

export const BOARD_LIMIT = 10;

export interface BoardFilters {
  search?: string;
  projectId?: string;
  filter?: string;
}

export function fetchBoards(
  limit: number,
  offset: number,
  filters: BoardFilters = {},
): Promise<PaginatedBoards> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  if (filters.search) params.set("search", filters.search);
  if (filters.projectId) params.set("project_id", filters.projectId);
  if (filters.filter) params.set("filter", filters.filter);
  return apiJson(`/api/v1/boards/?${params}`, "Failed to fetch boards");
}

export function fetchBoard(id: string): Promise<Board> {
  return apiJson(`/api/v1/boards/${id}`, "Failed to fetch board");
}

export function fetchBoardView(id: string): Promise<BoardView> {
  return apiJson(`/api/v1/boards/${id}/view`, "Failed to fetch board view");
}

export function createBoard(item: BoardCreate): Promise<Board> {
  return apiJson(
    "/api/v1/boards/",
    "Failed to create board",
    jsonBody("POST", item),
  );
}

export function updateBoard(id: string, item: BoardUpdate): Promise<Board> {
  return apiJson(
    `/api/v1/boards/${id}`,
    "Failed to update board",
    jsonBody("PATCH", item),
  );
}

export async function deleteBoard(id: string): Promise<void> {
  await apiFetch(`/api/v1/boards/${id}`, "Failed to delete board", {
    method: "DELETE",
  });
}
