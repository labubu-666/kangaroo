import { createFileRoute } from "@tanstack/react-router";
import { WorkflowPage } from "../../components/workflow/WorkflowPage";

export const Route = createFileRoute("/projects/$id_/statuses")({
  component: StatusesRoute,
});

function StatusesRoute() {
  const { id } = Route.useParams();
  return <WorkflowPage projectId={id} />;
}
