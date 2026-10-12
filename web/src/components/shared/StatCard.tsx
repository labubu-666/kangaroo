import { Link } from "@tanstack/react-router";

export function StatCard({
  label,
  value,
  to,
  search,
  className = "",
}: {
  label: string;
  value: number;
  to?: "/projects" | "/work-items";
  search?: { filter: string };
  className?: string;
}) {
  const content = (
    <>
      <div className="text-sm font-medium text-gray-600">{label}</div>
      <div className="mt-1 text-3xl font-bold">{value}</div>
    </>
  );
  const base = `block rounded border p-4 ${className}`;
  return to ? (
    <Link
      to={to}
      search={search}
      className={`${base} hover:border-blue-400 hover:bg-blue-50 transition`}
    >
      {content}
    </Link>
  ) : (
    <div className={base}>{content}</div>
  );
}
