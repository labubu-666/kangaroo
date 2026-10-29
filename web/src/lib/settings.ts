import { apiJson } from "./api";

export function fetchSettings(): Promise<Record<string, unknown>> {
  return apiJson("/api/v1/settings/", "Failed to fetch settings");
}
