import type { Page } from "@playwright/test";

// Stands in for the backend's recent history in component tests. Visits are kept
// newest first, reads return the 10 newest matches, and writes behave as the API does.
export async function fakeRecentHistory(page: Page, seed: object[] = []) {
  const items: Record<string, unknown>[] = [...seed].map((entry, index) => ({
    ...toApi(entry as Record<string, unknown>),
    modified_at: new Date(Date.UTC(2026, 0, 1, 0, 0, index)).toISOString(),
  }));
  const clock = () =>
    new Date(Date.UTC(2026, 0, 2, 0, 0, items.length)).toISOString();

  await page.route("**/api-internal/v1/recent-history**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const body = request.postDataJSON() as Record<string, unknown> | null;
    if (request.method() === "GET") {
      const search = (url.searchParams.get("search") ?? "").toLowerCase();
      const matches = items
        .filter(
          (item) =>
            !search ||
            String(item.title).toLowerCase().includes(search) ||
            String(item.parent ?? "")
              .toLowerCase()
              .includes(search),
        )
        .slice(0, 10);
      return route.fulfill({ json: matches });
    }
    if (request.method() === "POST" && body) {
      const index = items.findIndex(
        (item) => item.type === body.type && item.item_id === body.item_id,
      );
      if (index >= 0) items.splice(index, 1);
      items.unshift({ ...body, modified_at: clock() });
      return route.fulfill({ status: 204 });
    }
    if (request.method() === "DELETE") {
      const segments = url.pathname.split("/").filter(Boolean);
      if (segments.length > 3) {
        const [, , type, itemId] = segments.slice(-4);
        const index = items.findIndex(
          (item) => item.type === type && item.item_id === itemId,
        );
        if (index >= 0) items.splice(index, 1);
      } else {
        items.length = 0;
      }
      return route.fulfill({ status: 204 });
    }
    return route.fulfill({ status: 405 });
  });
}

function toApi(entry: Record<string, unknown>) {
  return {
    type: entry.type,
    item_id: entry.id,
    title: entry.title,
    parent: entry.parent ?? null,
    to: entry.to,
    params: entry.params,
    search: entry.search ?? {},
  };
}
