// Shown where finished work is counted, when the project has no Done status
export function DoneStatusWarning() {
  return (
    <div className="rounded-md border border-yellow-200 dark:border-yellow-900 bg-yellow-50 dark:bg-yellow-950 p-3 text-yellow-800 dark:text-yellow-200">
      No status is in the Done category, so finished work items can't be counted
      here. Add one in Statuses and types.
    </div>
  );
}
