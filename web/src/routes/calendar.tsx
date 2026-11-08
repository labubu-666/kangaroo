import { createFileRoute } from "@tanstack/react-router";
import { CalendarPage } from "../components/calendar/CalendarPage";
import { useBreadcrumbs } from "../components/breadcrumbs/BreadcrumbsContext";
import { useRecordRecent } from "../lib/recent";

export const Route = createFileRoute("/calendar")({
  component: CalendarRoute,
});

function CalendarRoute() {
  useBreadcrumbs([{ label: "Calendar" }]);
  useRecordRecent({
    type: "calendar",
    id: "all",
    title: "Calendar",
    to: "/calendar",
    params: {},
  });
  return (
    <div className="p-4">
      <CalendarPage />
    </div>
  );
}
