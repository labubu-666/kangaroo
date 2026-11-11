import { useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch, apiJson, jsonBody } from "./api";

export type RecentType =
  | "project"
  | "board"
  | "work-item"
  | "function"
  | "pipeline"
  | "article"
  | "knowledge-base"
  | "calendar"
  | "project-tab";

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
    | { type: "pipeline"; to: "/pipelines/$id"; params: { id: string } }
    | {
        type: "article";
        parent: string;
        to: "/articles/$id";
        params: { id: string };
      }
    | {
        type: "knowledge-base";
        to: "/knowledge-bases/$id";
        params: { id: string };
      }
    | { type: "calendar"; to: "/calendar"; params: Record<string, never> }
    | {
        type: "project-tab";
        parent: string;
        to: "/projects/$id";
        params: { id: string };
        search: { tab: string };
      }
  );

// The API's shape of one entry, before it is turned into a RecentEntry
interface RecentEntryResponse {
  type: RecentType;
  item_id: string;
  title: string;
  parent: string | null;
  to: string;
  params: Record<string, string>;
  search: Record<string, string>;
  modified_at: string;
}

const HISTORY_PATH = "/api-internal/v1/recent-history";
// The old browser-only copy of the list, removed once the backend takes over
const LEGACY_STORAGE_KEY = "kangaroo-recent";

// The API sends every type with the same fields. The stored `to` and `params`
// come from the page that recorded the visit, so they match the entry's type.
function fromResponse(item: RecentEntryResponse): RecentEntry {
  const base = { id: item.item_id, title: item.title };
  if (item.parent === null) {
    return {
      ...base,
      type: item.type,
      to: item.to,
      params: item.params,
      search: item.search,
    } as RecentEntry;
  }
  return {
    ...base,
    type: item.type,
    parent: item.parent,
    to: item.to,
    params: item.params,
    search: item.search,
  } as RecentEntry;
}

function toRequest(entry: RecentEntry) {
  return {
    type: entry.type,
    item_id: entry.id,
    title: entry.title,
    parent: "parent" in entry ? (entry.parent ?? null) : null,
    to: entry.to,
    params: entry.params,
    search: "search" in entry ? (entry.search ?? {}) : {},
  };
}

function historyKey(search: string) {
  return ["recent-history", search] as const;
}

export function useRecentEntries(search = "") {
  const trimmed = search.trim();
  useRefreshOnChange();
  const { data = [] } = useQuery({
    queryKey: historyKey(trimmed),
    queryFn: async () => {
      const query = trimmed ? `?search=${encodeURIComponent(trimmed)}` : "";
      const items = await apiJson<RecentEntryResponse[]>(
        `${HISTORY_PATH}/${query}`,
        "Failed to load recent history",
      );
      return items.map(fromResponse);
    },
  });
  return data;
}

// Pages that change an item outside React ask the list to refresh with this event
const CHANGED_EVENT = "kangaroo-recent-changed";

function useInvalidateHistory() {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: ["recent-history"] });
}

function useRefreshOnChange() {
  const invalidate = useInvalidateHistory();
  useEffect(() => {
    window.addEventListener(CHANGED_EVENT, invalidate);
    return () => window.removeEventListener(CHANGED_EVENT, invalidate);
  }, [invalidate]);
}

// Records a visit once per distinct entry. Pass undefined until the page's data has loaded.
export function useRecordRecent(entry: RecentEntry | undefined) {
  const invalidate = useInvalidateHistory();
  // Compare by value so pages can pass a new object on every render without looping
  const serialized = JSON.stringify(entry ?? null);
  useEffect(() => {
    const next: RecentEntry | null = JSON.parse(serialized);
    if (!next) return;
    // Plain request, not useMutation: the list refreshes whether or not the
    // component is still mounted when the visit is saved
    apiFetch(
      `${HISTORY_PATH}/`,
      "Failed to record recent item",
      jsonBody("POST", toRequest(next)),
    ).finally(invalidate);
  }, [serialized, invalidate]);
}

export function useClearRecent() {
  const invalidate = useInvalidateHistory();
  return useMutation({
    mutationFn: () =>
      apiFetch(`${HISTORY_PATH}/`, "Failed to clear recent history", {
        method: "DELETE",
      }),
    onSuccess: invalidate,
  });
}

// Pages call this from their delete handlers, outside React
export async function removeRecent(type: RecentType, id: string) {
  await apiFetch(
    `${HISTORY_PATH}/${type}/${encodeURIComponent(id)}`,
    "Failed to remove recent item",
    { method: "DELETE" },
  );
  window.dispatchEvent(new Event(CHANGED_EVENT));
}

// The browser copy of the list is no longer read, so drop it
export function clearLegacyRecent() {
  localStorage.removeItem(LEGACY_STORAGE_KEY);
}
