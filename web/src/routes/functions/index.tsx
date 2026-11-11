import { createFileRoute } from "@tanstack/react-router";
import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { FunctionList } from "../../components/functions/FunctionList";

export const Route = createFileRoute("/functions/")({
  component: FunctionsPage,
});

function FunctionsPage() {
  useBreadcrumbs([{ label: "Functions" }]);
  return (
    <div className="p-4">
      <FunctionList />
    </div>
  );
}
