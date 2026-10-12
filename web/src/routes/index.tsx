import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useBreadcrumbs } from "../components/breadcrumbs/BreadcrumbsContext";
import { ErrorBanner } from "../components/shared/ErrorBanner";
import { Loading } from "../components/shared/Loading";
import { StatCard } from "../components/shared/StatCard";
import { fetchSummary } from "../lib/reports";

export const Route = createFileRoute("/")({
  component: Home,
});

// Categories are fixed across projects, so these cards match on statusCategory
const STATUS_CARDS = [
  {
    key: "todo",
    label: "To do",
    className: "border-yellow-200 bg-yellow-50",
    to: "/work-items",
    search: { filter: "statusCategory == 'todo'" },
  },
  {
    key: "in_progress",
    label: "In progress",
    className: "border-blue-200 bg-blue-50",
    to: "/work-items",
    search: { filter: "statusCategory == 'in_progress'" },
  },
  {
    key: "done",
    label: "Done",
    className: "border-green-200 bg-green-50",
    to: "/work-items",
    search: { filter: "statusCategory == 'done'" },
  },
] as const;

function Home() {
  useBreadcrumbs([{ label: "Home", to: "/" }]);

  const { data, isLoading, error } = useQuery({
    queryKey: ["reports", "summary"],
    queryFn: fetchSummary,
  });

  return (
    <div className="space-y-6 p-4">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      {error && <ErrorBanner>Error loading summary</ErrorBanner>}

      {isLoading || !data ? (
        !error && <Loading />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-3">
            <StatCard label="Projects" value={data.projects} to="/projects" />
            <StatCard label="Boards" value={data.boards} />
            <StatCard
              label="Work items"
              value={data.work_items.total}
              to="/work-items"
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            {STATUS_CARDS.map((card) => (
              <StatCard
                key={card.key}
                label={card.label}
                value={data.work_items[card.key]}
                className={card.className}
                to={"to" in card ? card.to : undefined}
                search={"search" in card ? card.search : undefined}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
