import { useQuery } from "@tanstack/react-query";
import { fetchStatuses } from "../../lib/workflow";

// Picks one status of a single project. The choice is written into the list's
// filter, so the status id always belongs to the project in the filter.
export function StatusPicker({
  projectId,
  statusId,
  onChange,
}: {
  projectId: string;
  statusId?: string;
  onChange: (statusId: string | undefined) => void;
}) {
  const { data: statuses, error } = useQuery({
    queryKey: ["statuses", projectId],
    queryFn: () => fetchStatuses(projectId),
  });

  return (
    <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:gap-3">
      <label
        htmlFor="status-picker"
        className="text-sm font-medium text-fg-secondary"
      >
        Status
      </label>
      <select
        id="status-picker"
        value={statusId ?? ""}
        disabled={!statuses}
        onChange={(e) => onChange(e.target.value || undefined)}
        className="rounded border border-border-strong px-3 py-2"
      >
        <option value="">All statuses</option>
        {(statuses ?? []).map((status) => (
          <option key={status.id} value={status.id}>
            {status.name}
          </option>
        ))}
      </select>
      {error && (
        <span className="text-sm text-danger">Error loading statuses</span>
      )}
    </div>
  );
}
