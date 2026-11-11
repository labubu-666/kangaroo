import { Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { FUNCTION_LIMIT, fetchFunctions } from "../../lib/functions";
import { ErrorBanner } from "../shared/ErrorBanner";
import { Loading } from "../shared/Loading";
import { Pagination } from "../shared/Pagination";

export function FunctionList() {
  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState("");

  const { data, isLoading, error } = useQuery({
    queryKey: ["functions", offset, search],
    queryFn: () => fetchFunctions(FUNCTION_LIMIT, offset, search.trim()),
  });

  const items = data?.results ?? [];
  const total = data?.total ?? 0;

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
        <h2 className="text-xl font-semibold">Functions</h2>
        <Link
          to="/functions/create"
          className="rounded bg-primary px-4 py-2 text-center font-medium text-on-primary hover:bg-primary-hover"
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
        className="w-full rounded border border-border-strong px-3 py-2"
      />

      {error && <ErrorBanner>Error loading functions</ErrorBanner>}

      {isLoading ? (
        <Loading />
      ) : items.length === 0 ? (
        <div className="text-center text-fg-muted">
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
              className="flex flex-col gap-1 rounded border border-border p-4 hover:border-primary hover:bg-primary-subtle transition"
            >
              <h3 className="font-semibold text-primary">{fn.name}</h3>
              {fn.description && (
                <p className="text-sm text-fg-secondary">{fn.description}</p>
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
