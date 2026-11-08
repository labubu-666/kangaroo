import { useRecordRecent } from "../../lib/recent";

// Records the calendar visit the way the calendar route does
export function CalendarRecorder() {
  useRecordRecent({
    type: "calendar",
    id: "all",
    title: "Calendar",
    to: "/calendar",
    params: {},
  });
  return null;
}
