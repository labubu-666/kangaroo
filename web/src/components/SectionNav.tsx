import { Link } from "@tanstack/react-router";

export function SectionNav() {
  return (
    <nav
      aria-label="Sections"
      className="flex flex-wrap items-center gap-x-4 gap-y-2 px-4 pt-4"
    >
      <Link
        to="/"
        activeOptions={{ exact: true }}
        className="font-medium hover:underline"
        activeProps={{ className: "text-blue-600" }}
      >
        Home
      </Link>
      <Link
        to="/projects"
        className="font-medium hover:underline"
        activeProps={{ className: "text-blue-600" }}
      >
        Projects
      </Link>
      <Link
        to="/work-items"
        className="font-medium hover:underline"
        activeProps={{ className: "text-blue-600" }}
      >
        Work items
      </Link>
      <Link
        to="/functions"
        className="font-medium hover:underline"
        activeProps={{ className: "text-blue-600" }}
      >
        Functions
      </Link>
      <Link
        to="/articles"
        className="font-medium hover:underline"
        activeProps={{ className: "text-blue-600" }}
      >
        Knowledge base
      </Link>
    </nav>
  );
}
