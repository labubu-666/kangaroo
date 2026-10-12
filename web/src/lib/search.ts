import { fetchBoards, type PaginatedBoards } from "./boards";
import { fetchProjects, type PaginatedProjects } from "./projects";
import { fetchWorkItems, type PaginatedWorkItems } from "./work-items";

export interface SearchResults {
  workItems: PaginatedWorkItems;
  projects: PaginatedProjects;
  boards: PaginatedBoards;
}

// Searches work items, projects and boards for the same text in parallel
export async function searchAll(
  term: string,
  limit: number,
): Promise<SearchResults> {
  const [workItems, projects, boards] = await Promise.all([
    fetchWorkItems(limit, 0, { search: term }),
    fetchProjects(limit, 0, term),
    fetchBoards(limit, 0, { search: term }),
  ]);
  return { workItems, projects, boards };
}
