import { Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { fetchFunctions } from "../../lib/functions";
import type { Invocation } from "../../lib/invocations";
import { fetchInvocations, INVOCATION_LIMIT } from "../../lib/invocations";

import { STATUS_TEXT } from "../functions/RunOutput";
import { ErrorBanner } from "../shared/ErrorBanner";
import { Loading } from "../shared/Loading";
import { Pagination } from "../shared/Pagination";

export function InvocationList() {
  const [offset, setOffset] = useState(0);

  const { data, isLoading, error } = useQuery({
    queryKey: ["invocations", offset],
    queryFn: () => fetchInvocations(INVOCATION_LIMIT, offset),
  });

  const { data: functions } = useQuery({
    queryKey: ["functions", "names"],
    queryFn: () => fetchFunctions(100, 0),
  });

  const functionNames = new Map(
    (functions?.results ?? []).map((fn) => [fn.id, fn.name]),
  );

  const items: Invocation[] = data?.results ?? [];
  const total = data?.total ?? 0;

  return (
    <div className="space-y-4">
      {error && <ErrorBanner>Error loading invocations</ErrorBanner>}

      {isLoading ? (
        <Loading />
      ) : items.length === 0 ? (
        <div className="text-center text-gray-500">No invocations yet</div>
      ) : (
        <div className="flex flex-col gap-4">
          {items.map((invocation) => (
            <Link
              key={invocation.id}
              to="/invocations/$id"
              params={{ id: invocation.id }}
              className="flex flex-col gap-1 rounded border border-gray-200 p-4 hover:border-blue-400 hover:bg-blue-50 transition"
            >
              <div className="flex flex-wrap items-center gap-3">
                <h3 className="font-semibold text-blue-600">
                  {functionNames.get(invocation.function_id) ?? "Unknown"}
                </h3>
                <span
                  className={`text-sm font-medium ${STATUS_TEXT[invocation.status]}`}
                >
                  {invocation.status}
                </span>
              </div>
              <p className="text-xs text-gray-500">
                {new Date(invocation.created_at).toLocaleString()}
              </p>
            </Link>
          ))}
        </div>
      )}

      <Pagination
        offset={offset}
        limit={INVOCATION_LIMIT}
        total={total}
        disabled={isLoading}
        onChange={setOffset}
      />
    </div>
  );
}
