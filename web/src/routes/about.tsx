import { createFileRoute, Link } from "@tanstack/react-router";

export const Route = createFileRoute("/about")({
  component: About,
});

function About() {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold underline">About</h1>
      <p className="mt-4 text-gray-600">
        This is the about page — routing works!
      </p>
      <Link to="/" className="mt-4 inline-block text-blue-600 hover:underline">
        ← Back home
      </Link>
    </div>
  );
}
