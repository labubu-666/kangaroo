import { expect, test } from "../../../playwright/fixtures.ts";
import { TestRouter } from "../TestRouter.story";
import { ProjectWorkItemList } from "./ProjectWorkItemList";

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

test.describe("ProjectWorkItemList", () => {
  test("sends the project, sort and page to the API", async ({
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
    const component = await mount(
      <TestRouter paths={["/"]}>
        <ProjectWorkItemList
          projectId="p1"
          sort="summary"
          offset={10}
          onFilterChange={() => {}}
          onSortChange={() => {}}
          onOffsetChange={() => {}}
        />
      </TestRouter>,
    );
    await expect(component).toContainText("First item");
    const last = requests.at(-1);
    expect(last?.searchParams.get("project_id")).toBe("p1");
    expect(last?.searchParams.get("sort")).toBe("summary");
    expect(last?.searchParams.get("offset")).toBe("10");
  });

  test("reports sort and page changes", async ({ mount, page }) => {
    await page.route("**/api/v1/work-items/**", (route) =>
      route.fulfill({
        json: { results: ITEMS, limit: 10, offset: 0, total: 25 },
      }),
    );
    const sorts: string[] = [];
    const pages: number[] = [];
    const component = await mount(
      <TestRouter paths={["/"]}>
        <ProjectWorkItemList
          projectId="p1"
          sort="-modified_at"
          offset={0}
          onFilterChange={() => {}}
          onSortChange={(next) => sorts.push(next)}
          onOffsetChange={(next) => pages.push(next)}
        />
      </TestRouter>,
    );
    await expect(component).toContainText("First item");

    await component.getByLabel("Sort work items").selectOption("summary");
    expect(sorts).toEqual(["summary"]);

    await component.getByRole("button", { name: "2", exact: true }).click();
    expect(pages).toEqual([10]);
  });
});
