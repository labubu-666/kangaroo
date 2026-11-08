import type { Page } from "@playwright/test";
import { expect, test } from "../../../playwright/fixtures.ts";
import { TestRouter } from "../TestRouter.story";
import { BacklogPage } from "./BacklogPage";

const PROJECT = "01a1-proj";
const STAMP = {
  created_at: "2026-01-01T00:00:00Z",
  modified_at: "2026-01-01T00:00:00Z",
};
const STATUSES = [
  {
    id: "s-open",
    project_id: PROJECT,
    name: "Open",
    category: "todo",
    position: 0,
    ...STAMP,
  },
  {
    id: "s-done",
    project_id: PROJECT,
    name: "Done",
    category: "done",
    position: 1,
    ...STAMP,
  },
];
const STATUS = { id: "s-open", name: "Open", category: "todo" };
const TYPE = { id: "t-task", name: "Task" };

function item(id: string, summary: string) {
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
    due_at: null,
    trashed: false,
    ...STAMP,
  };
}

const PATHS = ["/", "/work-items/$id"];

async function stubApi(
  page: Page,
  workItems: { status?: number; json: unknown },
) {
  await page.route("**/api/v1/statuses/**", (route) =>
    route.fulfill({ json: STATUSES }),
  );
  await page.route("**/api/v1/work-items/**", (route) => {
    const filter =
      new URL(route.request().url()).searchParams.get("filter") ?? "";
    const statusId = filter.match(/'([^']+)'/)?.[1];
    if (workItems.status) {
      return route.fulfill({ status: workItems.status, json: workItems.json });
    }
    const json = workItems.json as { results: { status_id: string }[] };
    return route.fulfill({
      json: {
        ...(json as object),
        results: json.results.filter((w) => w.status_id === statusId),
      },
    });
  });
}

const ONE_ITEM = {
  json: {
    results: [item("w1", "Write docs")],
    limit: 50,
    offset: 0,
    total: 1,
  },
};

test.describe("BacklogPage", () => {
  test("shows a section per status with its items", async ({ mount, page }) => {
    await stubApi(page, ONE_ITEM);
    const component = await mount(
      <TestRouter paths={PATHS}>
        <BacklogPage projectId={PROJECT} />
      </TestRouter>,
    );
    await expect(component.getByRole("button", { name: "Open" })).toBeVisible();
    await expect(component.getByRole("button", { name: "Done" })).toBeVisible();
    await expect(component.getByText("Write docs")).toBeVisible();
  });

  test("collapses a section when its header is clicked", async ({
    mount,
    page,
  }) => {
    await stubApi(page, ONE_ITEM);
    const component = await mount(
      <TestRouter paths={PATHS}>
        <BacklogPage projectId={PROJECT} />
      </TestRouter>,
    );
    const toggle = component.getByRole("button", { name: "Open" });
    await expect(toggle).toHaveAttribute("aria-expanded", "true");
    await toggle.click();
    await expect(toggle).toHaveAttribute("aria-expanded", "false");
    await expect(component.getByText("Write docs")).toHaveCount(0);
  });

  test("says so when a status has no items", async ({ mount, page }) => {
    await stubApi(page, {
      json: { results: [], limit: 50, offset: 0, total: 0 },
    });
    const component = await mount(
      <TestRouter paths={PATHS}>
        <BacklogPage projectId={PROJECT} />
      </TestRouter>,
    );
    await expect(component.getByText("No items").first()).toBeVisible();
  });

  test("shows the error when the work items cannot load", async ({
    mount,
    page,
  }) => {
    await stubApi(page, {
      status: 500,
      json: { detail: "Database is down" },
    });
    const component = await mount(
      <TestRouter paths={PATHS}>
        <BacklogPage projectId={PROJECT} />
      </TestRouter>,
    );
    await expect(component.getByText("Database is down").first()).toBeVisible();
  });
});

test.describe("BacklogPage drag", () => {
  test("dragging a row onto another status sends the move", async ({
    mount,
    page,
  }) => {
    let moved: unknown = null;
    await stubApi(page, ONE_ITEM);
    await page.route("**/api/v1/work-items/w1", (route) => {
      if (route.request().method() === "PATCH") {
        moved = route.request().postDataJSON();
      }
      return route.fulfill({ json: item("w1", "Write docs") });
    });
    const component = await mount(
      <TestRouter paths={PATHS}>
        <BacklogPage projectId={PROJECT} />
      </TestRouter>,
    );
    const title = component.getByText("Write docs");
    const done = component.getByRole("button", { name: "Done" });
    const from = await title.boundingBox();
    const to = await done.boundingBox();
    await page.mouse.move(from!.x + 5, from!.y + from!.height / 2);
    await page.mouse.down();
    await page.mouse.move(from!.x + 20, from!.y + from!.height / 2, {
      steps: 5,
    });
    await page.mouse.move(to!.x + to!.width / 2, to!.y + to!.height / 2, {
      steps: 20,
    });
    await page.waitForTimeout(200);
    await page.mouse.up();

    await expect.poll(() => moved).toEqual({ status_id: "s-done" });
  });
});
