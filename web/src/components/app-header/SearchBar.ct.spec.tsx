import { expect, test } from "../../../playwright/fixtures.ts";
import { SearchBar } from "./SearchBar";
import { TestRouter } from "../TestRouter.story";

const paths = [
  "/",
  "/search",
  "/work-items/$id",
  "/projects/$id",
  "/projects/$id/boards/$boardId",
];

const workItems = {
  results: [
    {
      id: "3f2a9c1d-0000-4000-8000-000000000001",
      summary: "Login bug",
      description: null,
      rendered_description: null,
      project_id: "p1",
      status: "open",
      created_at: "2026-01-01T00:00:00Z",
      modified_at: "2026-01-01T00:00:00Z",
      labels: [],
      trashed: false,
      type: "task",
    },
  ],
  limit: 3,
  offset: 0,
  total: 1,
};

const projects = {
  results: [
    {
      id: "p1-0000-4000-8000-000000000002",
      name: "Login project",
      description: null,
      created_at: "2026-01-01T00:00:00Z",
      modified_at: "2026-01-01T00:00:00Z",
      labels: [],
    },
  ],
  limit: 3,
  offset: 0,
  total: 1,
};

const boards = {
  results: [],
  limit: 3,
  offset: 0,
  total: 0,
};

// Answers the three list endpoints the search bar queries
test.beforeEach(async ({ page }) => {
  await page.route("**/api/v1/work-items/**", (route) =>
    route.fulfill({ json: workItems }),
  );
  await page.route("**/api/v1/projects/**", (route) =>
    route.fulfill({ json: projects }),
  );
  await page.route("**/api/v1/boards/**", (route) =>
    route.fulfill({ json: boards }),
  );
});

test.describe("SearchBar", () => {
  test("renders a search combobox", async ({ mount }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <SearchBar />
      </TestRouter>,
    );
    await expect(
      component.getByRole("combobox", { name: "Search" }),
    ).toBeVisible();
  });

  test("shows grouped suggestions after typing", async ({ mount, page }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <SearchBar />
      </TestRouter>,
    );
    await component.getByRole("combobox", { name: "Search" }).fill("login");

    const list = page.getByRole("listbox", { name: "Search suggestions" });
    await expect(list).toBeVisible();
    await expect(list.getByRole("option")).toHaveCount(2);
    await expect(list).toContainText("Login bug");
    await expect(list).toContainText("Work items");
    await expect(list).toContainText("Login project");
    await expect(list).toContainText("Projects");
  });

  test("does not search for fewer than two characters", async ({
    mount,
    page,
  }) => {
    let requested = false;
    await page.route("**/api/v1/work-items/**", (route) => {
      requested = true;
      return route.fulfill({ json: workItems });
    });
    const component = await mount(
      <TestRouter paths={paths}>
        <SearchBar />
      </TestRouter>,
    );
    await component.getByRole("combobox", { name: "Search" }).fill("a");
    await page.waitForTimeout(500);
    expect(requested).toBe(false);
    await expect(
      page.getByRole("listbox", { name: "Search suggestions" }),
    ).toHaveCount(0);
  });

  test("moves the highlight with arrow keys", async ({ mount, page }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <SearchBar />
      </TestRouter>,
    );
    const input = component.getByRole("combobox", { name: "Search" });
    await input.fill("login");
    const options = page.getByRole("option");
    await expect(options).toHaveCount(2);

    await input.press("ArrowDown");
    await expect(options.nth(0)).toHaveAttribute("aria-selected", "true");
    await input.press("ArrowDown");
    await expect(options.nth(1)).toHaveAttribute("aria-selected", "true");
    await input.press("ArrowUp");
    await expect(options.nth(0)).toHaveAttribute("aria-selected", "true");
  });

  test("Enter without a highlight goes to the results page", async ({
    mount,
  }) => {
    const component = await mount(
      <TestRouter paths={paths} showLocation>
        <SearchBar />
      </TestRouter>,
    );
    const input = component.getByRole("combobox", { name: "Search" });
    await input.fill("login");
    await input.press("Enter");
    await expect(component.getByTestId("location")).toHaveText(
      "/search?q=login",
    );
  });

  test("Escape closes the suggestions", async ({ mount, page }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <SearchBar />
      </TestRouter>,
    );
    const input = component.getByRole("combobox", { name: "Search" });
    await input.fill("login");
    await expect(
      page.getByRole("listbox", { name: "Search suggestions" }),
    ).toBeVisible();
    await input.press("Escape");
    await expect(
      page.getByRole("listbox", { name: "Search suggestions" }),
    ).toHaveCount(0);
  });

  test("Enter on a highlighted suggestion goes to that item", async ({
    mount,
    page,
  }) => {
    const component = await mount(
      <TestRouter paths={paths} showLocation>
        <SearchBar />
      </TestRouter>,
    );
    const input = component.getByRole("combobox", { name: "Search" });
    await input.fill("login");
    await expect(
      page.getByRole("listbox", { name: "Search suggestions" }),
    ).toBeVisible();
    await input.press("ArrowDown");
    await input.press("Enter");
    await expect(component.getByTestId("location")).toHaveText(
      "/work-items/3f2a9c1d-0000-4000-8000-000000000001",
    );
  });

  test("clicking a suggestion goes to that item", async ({ mount, page }) => {
    const component = await mount(
      <TestRouter paths={paths} showLocation>
        <SearchBar />
      </TestRouter>,
    );
    await component.getByRole("combobox", { name: "Search" }).fill("login");
    await page
      .getByRole("listbox", { name: "Search suggestions" })
      .getByRole("link", { name: /Login project/ })
      .click();
    await expect(component.getByTestId("location")).toHaveText(
      "/projects/p1-0000-4000-8000-000000000002",
    );
  });

  test("shows boards in a Boards group and links to the board", async ({
    mount,
    page,
  }) => {
    await page.route("**/api/v1/boards/**", (route) =>
      route.fulfill({
        json: {
          results: [
            {
              id: "b1-0000-4000-8000-000000000003",
              name: "Login board",
              description: null,
              project_id: "p1-0000-4000-8000-000000000002",
              filter: null,
              created_at: "2026-01-01T00:00:00Z",
              modified_at: "2026-01-01T00:00:00Z",
            },
          ],
          limit: 3,
          offset: 0,
          total: 1,
        },
      }),
    );
    const component = await mount(
      <TestRouter paths={paths} showLocation>
        <SearchBar />
      </TestRouter>,
    );
    await component.getByRole("combobox", { name: "Search" }).fill("login");
    const list = page.getByRole("listbox", { name: "Search suggestions" });
    await expect(list.getByRole("option")).toHaveCount(3);
    await expect(list).toContainText("Login board");
    await expect(list).toContainText("Boards");

    await list.getByRole("link", { name: /Login board/ }).click();
    await expect(component.getByTestId("location")).toHaveText(
      "/projects/p1-0000-4000-8000-000000000002/boards/b1-0000-4000-8000-000000000003",
    );
  });

  test("shows no suggestions when nothing matches", async ({ mount, page }) => {
    await page.route("**/api/v1/work-items/**", (route) =>
      route.fulfill({
        json: { results: [], limit: 3, offset: 0, total: 0 },
      }),
    );
    await page.route("**/api/v1/projects/**", (route) =>
      route.fulfill({
        json: { results: [], limit: 3, offset: 0, total: 0 },
      }),
    );
    const component = await mount(
      <TestRouter paths={paths}>
        <SearchBar />
      </TestRouter>,
    );
    const input = component.getByRole("combobox", { name: "Search" });
    await input.fill("zzzz");
    await expect(input).toHaveAttribute("aria-expanded", "false");
    await expect(
      page.getByRole("listbox", { name: "Search suggestions" }),
    ).toHaveCount(0);
  });

  test("closes the suggestions when focus leaves the search bar", async ({
    mount,
    page,
  }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <SearchBar />
      </TestRouter>,
    );
    const input = component.getByRole("combobox", { name: "Search" });
    await input.fill("login");
    await expect(
      page.getByRole("listbox", { name: "Search suggestions" }),
    ).toBeVisible();
    await input.press("Tab");
    await expect(
      page.getByRole("listbox", { name: "Search suggestions" }),
    ).toHaveCount(0);
  });

  test("searches only once typing pauses, using the final term", async ({
    mount,
    page,
  }) => {
    const requestedUrls: string[] = [];
    await page.route("**/api/v1/work-items/**", (route) => {
      requestedUrls.push(route.request().url());
      return route.fulfill({ json: workItems });
    });
    const component = await mount(
      <TestRouter paths={paths}>
        <SearchBar />
      </TestRouter>,
    );
    const input = component.getByRole("combobox", { name: "Search" });
    await input.pressSequentially("login");
    await expect(
      page.getByRole("listbox", { name: "Search suggestions" }),
    ).toBeVisible();
    expect(requestedUrls.length).toBeGreaterThan(0);
    expect(requestedUrls.every((url) => url.includes("login"))).toBe(true);
  });
});
