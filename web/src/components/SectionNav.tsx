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
        activeProps={{ className: "text-primary" }}
      >
        Home
      </Link>
      <Link
        to="/projects"
        className="font-medium hover:underline"
        activeProps={{ className: "text-primary" }}
      >
        Projects
      </Link>
      <Link
        to="/work-items"
        className="font-medium hover:underline"
        activeProps={{ className: "text-primary" }}
      >
        Work items
      </Link>
      <Link
        to="/functions"
        className="font-medium hover:underline"
        activeProps={{ className: "text-primary" }}
      >
        Functions
      </Link>
      <Link
        to="/knowledge-bases"
        className="font-medium hover:underline"
        activeProps={{ className: "text-primary" }}
      >
        Knowledge bases
      </Link>
    </nav>
  );
}
