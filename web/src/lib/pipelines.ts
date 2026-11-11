import { apiFetch, apiJson, jsonBody, type Paginated } from "./api";

export interface PipelineStep {
  function_id: string;
  on_success: string[];
  on_failure: string[];
}

export interface Pipeline {
  id: string;
  name: string;
  description: string | null;
  steps: Record<string, PipelineStep>;
  labels: string[];
  created_at: string;
  modified_at: string;
}

export interface PipelineCreate {
  name: string;
  description?: string;
  steps: Record<string, PipelineStep>;
  labels?: string[];
}

export type PipelineStepStatus =
  | "PENDING"
  | "RUNNING"
  | "SUCCESS"
  | "FAILURE"
  | "SKIPPED";

export type PipelineRunStatus = "PENDING" | "RUNNING" | "SUCCESS" | "FAILURE";

export interface PipelineStepRun {
  step: string;
  status: PipelineStepStatus;
  invocation_id: string | null;
}

export interface PipelineRun {
  id: string;
  pipeline_id: string;
  status: PipelineRunStatus;
  steps: PipelineStepRun[];
  created_at: string;
  modified_at: string;
}

export type PaginatedPipelines = Paginated<Pipeline>;
export type PaginatedPipelineRuns = Paginated<PipelineRun>;

export const PIPELINE_LIMIT = 10;
export const RUN_LIMIT = 5;

export function fetchPipelines(
  limit: number,
  offset: number,
  search?: string,
): Promise<PaginatedPipelines> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  if (search) params.set("search", search);
  return apiJson(`/api/v1/pipelines/?${params}`, "Failed to fetch pipelines");
}

export function fetchPipeline(id: string): Promise<Pipeline> {
  return apiJson(`/api/v1/pipelines/${id}`, "Failed to fetch pipeline");
}

export function createPipeline(item: PipelineCreate): Promise<Pipeline> {
  return apiJson(
    "/api/v1/pipelines/",
    "Failed to create pipeline",
    jsonBody("POST", item),
  );
}

export function updatePipeline(
  id: string,
  item: PipelineCreate,
): Promise<Pipeline> {
  return apiJson(
    `/api/v1/pipelines/${id}`,
    "Failed to update pipeline",
    jsonBody("PUT", item),
  );
}

export async function deletePipeline(id: string): Promise<void> {
  await apiFetch(`/api/v1/pipelines/${id}`, "Failed to delete pipeline", {
    method: "DELETE",
  });
}

export function startPipelineRun(id: string): Promise<{ run_id: string }> {
  return apiJson(`/api/v1/pipelines/${id}/run`, "Failed to start pipeline", {
    method: "POST",
  });
}

export function fetchPipelineRuns(
  id: string,
  limit: number,
  offset: number,
): Promise<PaginatedPipelineRuns> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  return apiJson(
    `/api/v1/pipelines/${id}/runs?${params}`,
    "Failed to fetch runs",
  );
}

export function fetchPipelineRun(runId: string): Promise<PipelineRun> {
  return apiJson(`/api/v1/runs/${runId}`, "Failed to fetch run");
}

export function fetchRuns(
  limit: number,
  offset: number,
  pipelineId?: string,
): Promise<PaginatedPipelineRuns> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  if (pipelineId) params.set("pipeline_id", pipelineId);
  return apiJson(`/api/v1/runs/?${params}`, "Failed to fetch runs");
}
