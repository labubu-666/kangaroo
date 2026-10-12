export function Pagination({
  offset,
  limit,
  total,
  disabled,
  onChange,
}: {
  offset: number;
  limit: number;
  total: number;
  disabled: boolean;
  onChange: (offset: number) => void;
}) {
  const hasPrevPage = offset > 0;
  const hasNextPage = offset + limit < total;
  return (
    <div className="mt-8 flex flex-wrap items-center justify-between gap-4">
      <button
        onClick={() => onChange(Math.max(0, offset - limit))}
        disabled={!hasPrevPage || disabled}
        className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:bg-gray-400"
      >
        ← Previous
      </button>
      <span className="order-first w-full text-center text-sm text-gray-600 sm:order-none sm:w-auto">
        Showing {Math.min(offset + 1, total)}-{Math.min(offset + limit, total)}{" "}
        of {total}
      </span>
      <button
        onClick={() => onChange(offset + limit)}
        disabled={!hasNextPage || disabled}
        className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:bg-gray-400"
      >
        Next →
      </button>
    </div>
  );
}
