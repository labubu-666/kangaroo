import { createFileRoute } from "@tanstack/react-router";
import { CreateProjectForm } from "../../components/projects/CreateProjectForm";

export const Route = createFileRoute("/projects/create")({
  component: CreateProject,
});

function CreateProject() {
  return <CreateProjectForm />;
}
