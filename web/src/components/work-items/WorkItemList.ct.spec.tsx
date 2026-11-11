import { expect, test } from "../../../playwright/fixtures.ts";
import { TestRouter } from "../TestRouter.story";
import { WorkItemListSelection } from "./WorkItemListSelection.story";
import { WorkItemList } from "./WorkItemList";

const STAMP = {
  created_at: "2026-01-01T00:00:00Z",
  modified_at: "2026-01-01T00:00:00Z",
};
const STATUS = { id: "s-open", name: "Open", category: "todo" };
const TYPE = { id: "t-task", name: "Task" };

function item(id: string, summary: string) {
  return {
    id,
    summary,
    description: null,
    rendered_description: null,
    project_id: "p1",
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

  test("sends sort to the API", async ({ mount, page }) => {
    const requests: URL[] = [];
    await page.route("**/api/v1/work-items/**", (route) => {
      requests.push(new URL(route.request().url()));
      route.fulfill({
        json: { results: ITEMS, limit: 10, offset: 0, total: 2 },
      });
    });
    const component = await mount(
      <TestRouter paths={["/"]}>
        <WorkItemList sort="summary" />
      </TestRouter>,
    );
    await expect(component).toContainText("First item");
    expect(requests.at(-1)?.searchParams.get("sort")).toBe("summary");
  });

  test("uses the page from the parent and reports page changes", async ({
    mount,
    page,
  }) => {
    const requests: URL[] = [];
    await page.route("**/api/v1/work-items/**", (route) => {
      requests.push(new URL(route.request().url()));
      route.fulfill({
        json: { results: ITEMS, limit: 10, offset: 10, total: 25 },
      });
    });
    const changes: number[] = [];
    const component = await mount(
      <TestRouter paths={["/"]}>
        <WorkItemList
          offset={10}
          onOffsetChange={(next) => changes.push(next)}
        />
      </TestRouter>,
    );
    await expect(component).toContainText("First item");
    expect(requests.at(-1)?.searchParams.get("offset")).toBe("10");

    await component.getByRole("button", { name: "1", exact: true }).click();
    expect(changes).toEqual([0]);
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
