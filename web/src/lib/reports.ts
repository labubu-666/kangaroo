import { apiJson } from "./api";
import type { ProjectStatus } from "./workflow";

export interface StatusCount {
  status: ProjectStatus;
  count: number;
}

export interface WorkItemCounts {
  total: number;
  todo: number;
  in_progress: number;
  done: number;
  by_status: StatusCount[];
}

export interface ReportSummary {
  projects: number;
  boards: number;
  work_items: WorkItemCounts;
}

export function fetchSummary(): Promise<ReportSummary> {
  return apiJson("/api/v1/reports/summary", "Failed to fetch summary");
}
