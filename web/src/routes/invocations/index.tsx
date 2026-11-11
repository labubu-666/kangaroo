import { createFileRoute } from "@tanstack/react-router";
import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { InvocationList } from "../../components/invocations/InvocationList";

export const Route = createFileRoute("/invocations/")({
  component: InvocationsPage,
});

function InvocationsPage() {
  useBreadcrumbs([{ label: "Invocations" }]);
  return (
    <div className="p-4">
      <InvocationList />
    </div>
  );
}
