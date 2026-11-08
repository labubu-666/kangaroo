import type { Page } from "@playwright/test";
import { expect, test } from "../../../playwright/fixtures.ts";
import { TestRouter } from "../TestRouter.story";
import { CalendarPage } from "./CalendarPage";

const PROJECT = "01a1-proj";
const STAMP = {
  created_at: "2026-01-01T00:00:00Z",
  modified_at: "2026-01-01T00:00:00Z",
};
const STATUS = { id: "s-open", name: "Open", category: "todo" };
const TYPE = { id: "t-task", name: "Task" };

function item(id: string, summary: string, dueAt: string) {
  return {
    id,
    summary,
    description: null,
    rendered_description: null,
    project_id: PROJECT,
    status_id: STATUS.id,
    type_id: TYPE.id,
    status: STATUS,
    type: TYPE,
    parent_id: null,
    labels: [],
    due_at: dueAt,
    trashed: false,
    ...STAMP,
  };
}

const PATHS = ["/", "/work-items/$id"];

// The calendar opens on the current month, so items must fall inside it.
function thisMonth() {
  const now = new Date();
  return new Date(now.getFullYear(), now.getMonth(), 15, 12);
}

async function stubApi(page: Page, results: ReturnType<typeof item>[]) {
  await page.route("**/api/v1/work-items/**", (route) =>
    route.fulfill({
      json: { results, limit: 1000, offset: 0, total: results.length },
    }),
  );
}

test.describe("CalendarPage", () => {
  test("shows a due item on the calendar", async ({ mount, page }) => {
    await stubApi(page, [item("w1", "Write docs", thisMonth().toISOString())]);
    const component = await mount(
      <TestRouter paths={PATHS}>
        <CalendarPage projectId={PROJECT} />
      </TestRouter>,
    );
    await expect(component.getByText("Write docs")).toBeVisible();
  });

  test("opens the work item when its event is clicked", async ({
    mount,
    page,
  }) => {
    await stubApi(page, [item("w1", "Write docs", thisMonth().toISOString())]);
    const component = await mount(
      <TestRouter paths={PATHS} initialPath="/" showLocation>
        <CalendarPage projectId={PROJECT} />
      </TestRouter>,
    );
    await component.getByRole("link", { name: "Write docs" }).click();
    await expect(component.getByTestId("location")).toHaveText(
      "/work-items/w1",
    );
  });
});

test.describe("CalendarPage without a project", () => {
  test("shows items from every project", async ({ mount, page }) => {
    await stubApi(page, [
      item("w1", "Write docs", thisMonth().toISOString()),
      {
        ...item("w2", "Other project task", thisMonth().toISOString()),
        project_id: "other",
      },
    ]);
    const component = await mount(
      <TestRouter paths={PATHS}>
        <CalendarPage />
      </TestRouter>,
    );
    await expect(component.getByText("Write docs")).toBeVisible();
    await expect(component.getByText("Other project task")).toBeVisible();
  });
});
