import { useState } from "react";
import { Pagination } from "./Pagination";

// Test-only wrapper: keeps the offset in state and exposes it so tests can assert on it
export function PaginationHarness({
  total,
  limit,
}: {
  total: number;
  limit: number;
}) {
  const [offset, setOffset] = useState(0);
  return (
    <>
      <output data-testid="offset">{offset}</output>
      <Pagination
        offset={offset}
        limit={limit}
        total={total}
        disabled={false}
        onChange={setOffset}
      />
    </>
  );
}
