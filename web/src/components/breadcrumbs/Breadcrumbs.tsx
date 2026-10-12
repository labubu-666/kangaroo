import { Link } from "@tanstack/react-router";

export interface BreadcrumbItem {
  label: string;
  to?: string;
  params?: Record<string, string>;
  search?: Record<string, string | undefined>;
}

export function Breadcrumbs({ items: pageItems }: { items: BreadcrumbItem[] }) {
  // The home page publishes its own root item, so don't add a second Home in front
  const items: BreadcrumbItem[] =
    pageItems[0]?.to === "/"
      ? pageItems
      : [{ label: "Home", to: "/" }, ...pageItems];
  return (
    <nav aria-label="Breadcrumb">
      <ol className="flex flex-wrap items-center gap-2 text-sm text-gray-500">
        {items.map((item, index) => {
          const isLast = index === items.length - 1;
          return (
            <li
              key={`${index}-${item.label}`}
              className="flex items-center gap-2"
            >
              {index > 0 && <span aria-hidden="true">/</span>}
              {isLast || !item.to ? (
                <span
                  aria-current={isLast ? "page" : undefined}
                  className="text-gray-700"
                >
                  {item.label}
                </span>
              ) : (
                <Link
                  to={item.to}
                  params={item.params}
                  search={item.search}
                  className="text-blue-600 hover:text-blue-700 hover:underline"
                >
                  {item.label}
                </Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
