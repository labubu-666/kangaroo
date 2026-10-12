import { apiJson } from "./api";

export interface ProjectTemplateList {
  default: string;
  names: string[];
}

// The templates a new project can be created from; the first is the default
export function fetchProjectTemplates(): Promise<ProjectTemplateList> {
  return apiJson(
    "/api/v1/project-templates/",
    "Failed to fetch project templates",
  );
}
