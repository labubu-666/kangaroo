const WINDOW_SIZE = 10;

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
  const totalPages = Math.max(1, Math.ceil(total / limit));

  const currentPage = Math.floor(offset / limit) + 1;
  // Shows a window of pages around the current one, so the row stays short on long lists.
  const start = Math.max(
    1,
    Math.min(currentPage - 4, totalPages - WINDOW_SIZE + 1),
  );
  const end = Math.min(totalPages, start + WINDOW_SIZE - 1);
  const pages = Array.from({ length: end - start + 1 }, (_, i) => start + i);

  const goToPage = (page: number) => onChange((page - 1) * limit);
  const hasPrevPage = currentPage > 1;
  const hasNextPage = currentPage < totalPages;

  return (
    <nav className="mt-8 flex flex-wrap items-center justify-center gap-3 text-sm">
      <button
        onClick={() => goToPage(currentPage - 1)}
        disabled={!hasPrevPage || disabled}
        className="flex items-center gap-1 px-2 py-1 text-primary hover:underline disabled:text-fg-disabled disabled:no-underline"
      >
        <span className="text-lg">‹</span> Previous
      </button>
      <ul className="flex items-center gap-3">
        {pages.map((page) => (
          <li key={page}>
            <button
              onClick={() => goToPage(page)}
              disabled={disabled}
              aria-current={page === currentPage ? "page" : undefined}
              className={
                page === currentPage
                  ? "min-w-6 font-semibold text-fg"
                  : "min-w-6 text-primary hover:underline"
              }
            >
              {page}
            </button>
          </li>
        ))}
      </ul>
      <button
        onClick={() => goToPage(currentPage + 1)}
        disabled={!hasNextPage || disabled}
        className="flex items-center gap-1 px-2 py-1 text-primary hover:underline disabled:text-fg-disabled disabled:no-underline"
      >
        Next <span className="text-lg">›</span>
      </button>
    </nav>
  );
}
