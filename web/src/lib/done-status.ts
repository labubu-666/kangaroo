// True when a project has statuses but none of them is in the Done category.
// Finished work items can't be counted without one.
export function lacksDoneStatus(categories: string[]): boolean {
  return categories.length > 0 && !categories.includes("done");
}
