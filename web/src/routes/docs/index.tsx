import { createFileRoute } from "@tanstack/react-router";
import { Doc } from "../../components/Doc";

export const Route = createFileRoute("/docs/")({
  component: () => <Doc name="index" />,
});
