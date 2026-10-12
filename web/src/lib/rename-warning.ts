import { filterUsesStatusName } from "./filter-bubbles";
import type { Board } from "./boards";

// The boards whose saved filter names this status, so renaming it would stop them matching
export function boardsUsingStatusName(boards: Board[], name: string): Board[] {
  return boards.filter((board) => filterUsesStatusName(board.filter, name));
}
