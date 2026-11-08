import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/react/daygrid";
import classicThemePlugin from "@fullcalendar/react/themes/classic";
import "@fullcalendar/react/skeleton.css";
import "@fullcalendar/react/themes/classic/theme.css";
import "@fullcalendar/react/themes/classic/palette.css";
import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { useState } from "react";
import { fetchWorkItems, WORK_ITEM_LIMIT } from "../../lib/work-items";
import { ErrorBanner } from "../shared/ErrorBanner";
import { Loading } from "../shared/Loading";

// Items are fetched for the month on screen. The API returns due dates as
// instants, and the calendar places them on the day they fall on in local time.
// Without a project, the calendar shows items from every project.
export function CalendarPage({ projectId }: { projectId?: string }) {
  const [range, setRange] = useState<{ from: Date; to: Date } | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: [
      "work-items",
      "calendar",
      projectId ?? null,
      range?.from.toISOString(),
    ],
    queryFn: () =>
      fetchWorkItems(WORK_ITEM_LIMIT * 10, 0, {
        projectId,
        dueFrom: range?.from.toISOString(),
        dueTo: range?.to.toISOString(),
      }),
    enabled: range !== null,
  });

  return (
    <div className="space-y-4">
      {error && <ErrorBanner>Error loading calendar</ErrorBanner>}
      {isLoading && range && <Loading />}
      <FullCalendar
        plugins={[dayGridPlugin, classicThemePlugin]}
        initialView="dayGridMonth"
        height="auto"
        datesSet={(info) => setRange({ from: info.start, to: info.end })}
        events={(data?.results ?? []).map((item) => ({
          id: item.id,
          title: item.summary,
          start: item.due_at ?? undefined,
          allDay: false,
        }))}
        eventContent={(arg) => (
          <Link
            to="/work-items/$id"
            params={{ id: arg.event.id }}
            className="block truncate px-1"
          >
            {arg.event.title}
          </Link>
        )}
      />
    </div>
  );
}
