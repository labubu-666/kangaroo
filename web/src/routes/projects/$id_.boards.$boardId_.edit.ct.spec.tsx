import { expect, test } from "../../../playwright/fixtures.ts";
import { TestRouter } from "../../components/TestRouter.story";
import { EditBoard } from "./$id_.boards.$boardId_.edit";

const PROJECT = "01a1-proj";
const OTHER_PROJECT = "01a2-other";
const BOARD = "b-1";
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
const PROJECT_JSON = {
  id: PROJECT,
  name: "Alpha",
  description: null,
  labels: [],
  ...STAMP,
};
const BOARD_JSON = {
  id: BOARD,
  name: "Sprint",
  description: null,
  project_id: PROJECT,
  filter: null,
  labels: [],
  status_order: ["s-done", "s-open"],
  hidden_status_ids: ["s-prog"],
  ...STAMP,
};
const PATHS = ["/projects/$id/boards/$boardId/edit"];
const INITIAL = `/projects/${PROJECT}/boards/${BOARD}/edit`;

// Answers the endpoints the page reads and records the board PATCH body
async function stubApi(page: {
  route: (url: string, handler: (route: any) => unknown) => Promise<unknown>;
}) {
  const sent: { body: Record<string, unknown> | null } = { body: null };
  await page.route("**/api/v1/projects/*", (route) =>
    route.fulfill({ json: PROJECT_JSON }),
  );
  await page.route("**/api/v1/projects/?*", (route) =>
    route.fulfill({
      json: {
        results: [
          PROJECT_JSON,
          { ...PROJECT_JSON, id: OTHER_PROJECT, name: "Beta" },
        ],
        limit: 50,
        offset: 0,
        total: 2,
      },
    }),
  );
  await page.route("**/api/v1/statuses/**", (route) =>
    route.fulfill({ json: STATUSES }),
  );
  await page.route("**/api/v1/boards/**", (route) => {
    if (route.request().method() === "PATCH") {
      sent.body = route.request().postDataJSON();
    }
    return route.fulfill({ json: BOARD_JSON });
  });
  return sent;
}

test.describe("board edit columns", () => {
  test("lists statuses in the saved column order", async ({ mount, page }) => {
    await stubApi(page);
    const component = await mount(
      <TestRouter paths={PATHS} initialPath={INITIAL}>
        <EditBoard />
      </TestRouter>,
    );
    const rows = component.getByRole("listitem");
    await expect(rows.nth(0)).toContainText("Done");
    await expect(rows.nth(1)).toContainText("Open");
    await expect(rows.nth(2)).toContainText("In Progress");
  });

  test("unchecks a hidden status", async ({ mount, page }) => {
    await stubApi(page);
    const component = await mount(
      <TestRouter paths={PATHS} initialPath={INITIAL}>
        <EditBoard />
      </TestRouter>,
    );
    await expect(component.getByLabel("In Progress")).not.toBeChecked();
    await expect(component.getByLabel("Done")).toBeChecked();
  });

  test("enables Save after a move and sends the new order", async ({
    mount,
    page,
  }) => {
    const sent = await stubApi(page);
    const component = await mount(
      <TestRouter paths={PATHS} initialPath={INITIAL}>
        <EditBoard />
      </TestRouter>,
    );
    const save = component.getByRole("button", { name: "Save" });
    await expect(save).toBeDisabled();

    await component
      .getByRole("listitem")
      .nth(1)
      .getByRole("button", { name: "Move up" })
      .click();
    await expect(save).toBeEnabled();
    await save.click();

    await expect.poll(() => sent.body).not.toBeNull();
    expect(sent.body).toMatchObject({
      status_order: ["s-open", "s-done", "s-prog"],
      hidden_status_ids: ["s-prog"],
    });
  });

  test("leaves column settings out when the project changes", async ({
    mount,
    page,
  }) => {
    const sent = await stubApi(page);
    const component = await mount(
      <TestRouter paths={PATHS} initialPath={INITIAL}>
        <EditBoard />
      </TestRouter>,
    );
    await component.getByLabel("Project").selectOption(OTHER_PROJECT);
    await component.getByRole("button", { name: "Save" }).click();

    await expect.poll(() => sent.body).not.toBeNull();
    expect(sent.body).not.toHaveProperty("status_order");
    expect(sent.body).not.toHaveProperty("hidden_status_ids");
  });
});
