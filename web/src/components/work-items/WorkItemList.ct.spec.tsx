import { expect, test } from "../../../playwright/fixtures.ts";
import { TestRouter } from "../TestRouter.story";
import { WorkItemListSelection } from "./WorkItemListSelection.story";
import { WorkItemList } from "./WorkItemList";

const STAMP = {
  created_at: "2026-01-01T00:00:00Z",
  modified_at: "2026-01-01T00:00:00Z",
};
const STATUS = { id: "s-open", name: "Open", category: "todo" };
const TYPE = { id: "t-task", name: "Task", level: "standard" };

function item(id: string, title: string) {
  return {
    id,
    title,
    description: null,
    rendered_description: null,
    project_id: "p1",
    status_id: STATUS.id,
    type_id: TYPE.id,
    status: STATUS,
    type: TYPE,
    parent_id: null,
    labels: [],
    trashed: false,
    ...STAMP,
  };
}

const ITEMS = [item("a", "First item"), item("b", "Second item")];

test.describe("WorkItemList selection", () => {
  test("checking rows and select-all updates the selection", async ({
    mount,
    page,
  }) => {
    await page.route("**/api/v1/work-items/**", (route) =>
      route.fulfill({
        json: { results: ITEMS, limit: 10, offset: 0, total: 2 },
      }),
    );
    const selections: string[][] = [];
    const component = await mount(
      <TestRouter paths={["/"]}>
        <WorkItemListSelection onChange={(ids) => selections.push(ids)} />
      </TestRouter>,
    );

    await component.getByLabel("Select First item").check();
    await expect(component.getByTestId("selected")).toHaveText("a");

    await component.getByLabel("Select all on this page").check();
    await expect(component.getByTestId("selected")).toHaveText("a,b");

    await component.getByLabel("Select all on this page").uncheck();
    await expect(component.getByTestId("selected")).toHaveText("");
  });

  test("reports the total to the parent", async ({ mount, page }) => {
    await page.route("**/api/v1/work-items/**", (route) =>
      route.fulfill({
        json: { results: ITEMS, limit: 10, offset: 0, total: 42 },
      }),
    );
    const component = await mount(
      <TestRouter paths={["/"]}>
        <WorkItemListSelection onChange={() => {}} />
      </TestRouter>,
    );
    await expect(component.getByTestId("total")).toHaveText("42");
  });

  test("shows no checkboxes without a selection", async ({ mount, page }) => {
    await page.route("**/api/v1/work-items/**", (route) =>
      route.fulfill({
        json: { results: ITEMS, limit: 10, offset: 0, total: 2 },
      }),
    );
    const component = await mount(
      <TestRouter paths={["/"]}>
        <WorkItemList />
      </TestRouter>,
    );
    await expect(component).toContainText("First item");
    await expect(component.getByRole("checkbox")).toHaveCount(0);
  });
});
