import { apiJson } from "./api";

export interface Doc {
  name: string;
  html: string;
}

export function fetchDoc(name: string): Promise<Doc> {
  return apiJson<Doc>(
    `/api/v1/docs/${encodeURIComponent(name)}`,
    "Failed to load doc",
  );
}
