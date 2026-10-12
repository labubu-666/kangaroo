import { expect, test } from "../../../playwright/fixtures.ts";
import { TestRouter } from "../../components/TestRouter.story";
import { WorkflowPage } from "../../components/workflow/WorkflowPage";

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
    id: "s-prog",
    project_id: PROJECT,
    name: "In Progress",
    category: "in_progress",
    position: 1,
    ...STAMP,
  },
  {
    id: "s-done",
    project_id: PROJECT,
    name: "Done",
    category: "done",
    position: 2,
    ...STAMP,
  },
];
const TYPES = [
  {
    id: "t-task",
    project_id: PROJECT,
    name: "Task",
    level: "standard",
    position: 0,
    ...STAMP,
  },
];

// Answers the endpoints the page reads. A status delete is answered by `onDelete`.
type RoutablePage = {
  route: (url: string, handler: (route: Route) => unknown) => Promise<unknown>;
};
type Route = {
  request: () => { method: () => string; url: () => string };
  fulfill: (options: { status?: number; json?: unknown }) => unknown;
};

async function stubApi(
  page: RoutablePage,
  options: {
    statuses?: unknown[];
    onDelete?: (url: URL) => { status: number; json?: unknown };
  } = {},
) {
  await page.route("**/api/v1/projects/**", (route) =>
    route.fulfill({
      json: {
        id: PROJECT,
        name: "Alpha",
        description: null,
        labels: [],
        ...STAMP,
      },
    }),
  );
  await page.route("**/api/v1/statuses/**", (route) => {
    if (route.request().method() === "DELETE") {
      const reply = options.onDelete?.(new URL(route.request().url())) ?? {
        status: 204,
      };
      return reply.status === 204
        ? route.fulfill({ status: 204 })
        : route.fulfill({ status: reply.status, json: reply.json });
    }
    return route.fulfill({ json: options.statuses ?? STATUSES });
  });
  await page.route("**/api/v1/work-item-types/**", (route) =>
    route.fulfill({ json: TYPES }),
  );
  await page.route("**/api/v1/status-transitions/**", (route) =>
    route.fulfill({ json: [] }),
  );
}

const PATHS = ["/projects/$id", "/projects/$id/statuses"];
const INITIAL = `/projects/${PROJECT}/statuses`;

test.describe("statuses and types page", () => {
  test("lists the project's statuses", async ({ mount, page }) => {
    await stubApi(page);
    const component = await mount(
      <TestRouter paths={PATHS} initialPath={INITIAL}>
        <WorkflowPage projectId={PROJECT} />
      </TestRouter>,
    );
    await expect(component.getByLabel("Name of In Progress")).toHaveValue(
      "In Progress",
    );
    await expect(
      component.getByRole("heading", { name: "Statuses", exact: true }),
    ).toBeVisible();
  });

  test("warns when no status is in the Done category", async ({
    mount,
    page,
  }) => {
    await stubApi(page, {
      statuses: STATUSES.filter((s) => s.category !== "done"),
    });
    const component = await mount(
      <TestRouter paths={PATHS} initialPath={INITIAL}>
        <WorkflowPage projectId={PROJECT} />
      </TestRouter>,
    );
    await expect(component).toContainText("No status is in the Done category");
  });

  test("an in-use status opens the replacement dialog", async ({
    mount,
    page,
  }) => {
    await stubApi(page, {
      onDelete: (url) =>
        url.searchParams.get("replacement_id")
          ? { status: 204 }
          : {
              status: 409,
              json: {
                detail: "2 work items use this status; choose a replacement",
              },
            },
    });
    const component = await mount(
      <TestRouter paths={PATHS} initialPath={INITIAL}>
        <WorkflowPage projectId={PROJECT} />
      </TestRouter>,
    );
    await component.getByRole("button", { name: "Delete In Progress" }).click();
    const dialog = component.getByRole("dialog");
    await expect(dialog).toContainText("2 work items use this status");
    await expect(
      dialog.getByRole("button", { name: "Delete and move items" }),
    ).toBeDisabled();
  });
});
