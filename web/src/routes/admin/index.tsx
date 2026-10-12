import { createFileRoute, Link } from "@tanstack/react-router";

import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";

export const Route = createFileRoute("/admin/")({
  component: Admin,
});

function Admin() {
  useBreadcrumbs([{ label: "Admin" }]);

  return (
    <div className="space-y-4 p-4 sm:p-8">
      <h1 className="text-2xl font-bold">Admin</h1>

      <section className="space-y-2">
        <h2 className="text-xl font-semibold">Work items</h2>
        <ul className="list-disc space-y-2 pl-5">
          <li>
            <Link
              to="/admin/work-items"
              className="text-blue-600 hover:underline"
            >
              All work items
            </Link>
          </li>
          <li>
            <Link
              to="/admin/work-items"
              search={{ filter: "trashed == true" }}
              className="text-blue-600 hover:underline"
            >
              Trashed work items
            </Link>
          </li>
        </ul>
      </section>
    </div>
  );
}
