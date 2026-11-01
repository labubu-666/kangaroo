import { fetchArticles, type PaginatedArticles } from "./articles";
import { fetchBoards, type PaginatedBoards } from "./boards";
import {
  fetchKnowledgeBases,
  type PaginatedKnowledgeBases,
} from "./knowledge-bases";
import { fetchProjects, type PaginatedProjects } from "./projects";
import { fetchWorkItems, type PaginatedWorkItems } from "./work-items";

export interface SearchResults {
  workItems: PaginatedWorkItems;
  projects: PaginatedProjects;
  boards: PaginatedBoards;
  knowledgeBases: PaginatedKnowledgeBases;
  articles: PaginatedArticles;
}

// Searches every entity type for the same text in parallel
export async function searchAll(
  term: string,
  limit: number,
): Promise<SearchResults> {
  const [workItems, projects, boards, knowledgeBases, articles] =
    await Promise.all([
      fetchWorkItems(limit, 0, { search: term }),
      fetchProjects(limit, 0, term),
      fetchBoards(limit, 0, { search: term }),
      fetchKnowledgeBases(limit, 0, term),
      fetchArticles(limit, 0, undefined, term),
    ]);
  return { workItems, projects, boards, knowledgeBases, articles };
}
