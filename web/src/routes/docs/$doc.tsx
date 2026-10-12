import { createFileRoute } from "@tanstack/react-router";
import { Doc } from "../../components/Doc";

export const Route = createFileRoute("/docs/$doc")({
  component: DocRoute,
});

function DocRoute() {
  const { doc } = Route.useParams();
  return <Doc name={doc} />;
}
