import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { FUNCTION_LIMIT, fetchFunctions } from "../../lib/functions";
import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { ErrorBanner } from "../../components/shared/ErrorBanner";
import { Loading } from "../../components/shared/Loading";
import { Pagination } from "../../components/shared/Pagination";

export const Route = createFileRoute("/functions/")({
  component: FunctionsList,
});

function FunctionsList() {
  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState("");

  useBreadcrumbs([{ label: "Functions" }]);

  const { data, isLoading, error } = useQuery({
    queryKey: ["functions", offset, search],
    queryFn: () => fetchFunctions(FUNCTION_LIMIT, offset, search.trim()),
  });

  const items = data?.results ?? [];
  const total = data?.total ?? 0;

  return (
    <div className="space-y-4 p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
        <h1 className="text-2xl font-bold">Functions</h1>
        <Link
          to="/functions/create"
          className="rounded bg-blue-600 px-4 py-2 text-center font-medium text-white hover:bg-blue-700"
        >
          New function
        </Link>
      </div>

      <input
        type="search"
        aria-label="Search functions"
        placeholder="Search functions"
        value={search}
        onChange={(e) => {
          setSearch(e.target.value);
          setOffset(0);
        }}
        className="w-full rounded border border-gray-300 px-3 py-2"
      />

      {error && <ErrorBanner>Error loading functions</ErrorBanner>}

      {isLoading ? (
        <Loading />
      ) : items.length === 0 ? (
        <div className="text-center text-gray-500">
          {search.trim()
            ? "No functions match this search"
            : "No functions yet"}
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {items.map((fn) => (
            <Link
              key={fn.id}
              to="/functions/$id"
              params={{ id: fn.id }}
              className="flex flex-col gap-1 rounded border border-gray-200 p-4 hover:border-blue-400 hover:bg-blue-50 transition"
            >
              <h3 className="font-semibold text-blue-600">{fn.name}</h3>
              {fn.description && (
                <p className="text-sm text-gray-600">{fn.description}</p>
              )}
            </Link>
          ))}
        </div>
      )}

      <Pagination
        offset={offset}
        limit={FUNCTION_LIMIT}
        total={total}
        disabled={isLoading}
        onChange={setOffset}
      />
    </div>
  );
}
