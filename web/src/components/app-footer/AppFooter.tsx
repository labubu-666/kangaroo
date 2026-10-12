import { Link } from "@tanstack/react-router";

export function AppFooter() {
  return (
    <footer className="mt-auto flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-gray-200 p-4 text-sm text-gray-600">
      <span>v0.0.0</span>
      <Link to="/docs" className="ml-auto font-medium hover:underline">
        Docs
      </Link>
      <a
        href="/api/v1/docs"
        target="_blank"
        rel="noopener noreferrer"
        className="font-medium hover:underline"
      >
        API
      </a>
    </footer>
  );
}
