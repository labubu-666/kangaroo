import { useDraggable } from "@dnd-kit/react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { fetchCurrentUser } from "../../lib/user";
import type { WorkItem } from "../../lib/work-items";
import { CopyId } from "../shared/CopyId";
import { TypeIcon } from "../shared/TypeIcon";

export function BoardCard({ item }: { item: WorkItem }) {
  const { ref, isDragging } = useDraggable({
    id: item.id,
    data: { status: item.status_id },
  });
  const { data: user } = useQuery({
    queryKey: ["user"],
    queryFn: fetchCurrentUser,
  });

  return (
    <Link
      ref={ref}
      to="/work-items/$id"
      params={{ id: item.id }}
      className={`flex cursor-pointer flex-col gap-3 rounded border border-border bg-surface p-3 shadow-sm hover:bg-surface-muted ${
        isDragging ? "opacity-50" : ""
      }`}
    >
      <div className="flex items-center gap-2">
        <TypeIcon type={item.type} />
        <p className="min-w-0 flex-1 truncate font-medium text-fg">
          {item.summary}
        </p>
      </div>
      {item.labels.length > 0 && (
        <ul className="flex flex-wrap gap-1">
          {item.labels.map((label) => (
            <li
              key={label}
              className="rounded bg-surface-strong px-2 py-0.5 text-xs font-medium text-fg-secondary"
            >
              {label}
            </li>
          ))}
        </ul>
      )}
      <div className="flex items-center justify-between gap-2 text-xs text-fg-muted">
        <div className="flex min-w-0 items-center gap-2">
          <CopyId
            id={item.id}
            prefix=""
            display={item.id}
            url={`${window.location.origin}/web/work-items/${item.id}`}
          />
        </div>
        {user ? (
          <img
            src={user.avatar_url}
            alt={user.username}
            className="h-6 w-6 shrink-0 border border-border"
          />
        ) : (
          <span
            aria-label="Unassigned"
            className="h-6 w-6 shrink-0 rounded-full bg-border-strong"
          />
        )}
      </div>
    </Link>
  );
}
