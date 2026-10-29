import { useEffect, useSyncExternalStore } from "react";

export type RecentType =
  | "project"
  | "board"
  | "work-item"
  | "function"
  | "article";

interface RecentBase {
  id: string;
  title: string;
}

// `parent` is the project or knowledge base the entry belongs to
export type RecentEntry = RecentBase &
  (
    | { type: "project"; to: "/projects/$id"; params: { id: string } }
    | {
        type: "board";
        parent: string;
        to: "/projects/$id/boards/$boardId";
        params: { id: string; boardId: string };
      }
    | {
        type: "work-item";
        parent: string;
        to: "/work-items/$id";
        params: { id: string };
      }
    | { type: "function"; to: "/functions/$id"; params: { id: string } }
    | {
        type: "article";
        parent: string;
        to: "/articles/$id";
        params: { id: string };
      }
  );

const STORAGE_KEY = "kangaroo-recent";
const LIMIT = 10;
const EMPTY: RecentEntry[] = [];
const listeners = new Set<() => void>();
let entries: RecentEntry[] | null = null;

// Cached in memory so useSyncExternalStore gets the same array until something changes
function load(): RecentEntry[] {
  if (entries) return entries;
  try {
    const parsed: unknown = JSON.parse(
      localStorage.getItem(STORAGE_KEY) ?? "[]",
    );
    entries = Array.isArray(parsed) ? (parsed as RecentEntry[]) : EMPTY;
  } catch {
    // Corrupt storage should not break the page
    entries = EMPTY;
  }
  return entries;
}

function save(next: RecentEntry[]) {
  entries = next;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function useRecentEntries() {
  return useSyncExternalStore(subscribe, load, () => EMPTY);
}

function recordRecent(entry: RecentEntry) {
  const others = load().filter(
    (item) => !(item.type === entry.type && item.id === entry.id),
  );
  save([entry, ...others].slice(0, LIMIT));
}

// Called by a detail page once its data has loaded; pass undefined until then
export function useRecordRecent(entry: RecentEntry | undefined) {
  // Compare by value so pages can pass a new object on every render without looping
  const serialized = JSON.stringify(entry ?? null);
  useEffect(() => {
    const next: RecentEntry | null = JSON.parse(serialized);
    if (next) recordRecent(next);
  }, [serialized]);
}

export function removeRecent(type: RecentType, id: string) {
  save(load().filter((item) => !(item.type === type && item.id === id)));
}

export function clearRecent() {
  save([]);
}
