import { expect, test } from "../../../playwright/fixtures.ts";
import { TestRouter } from "../TestRouter.story";
import type { RecentEntry } from "../../lib/recent";
import { RecentSection } from "./RecentSection";
import { Sidebar } from "./Sidebar";
import { SidebarProvider } from "./SidebarContext";
import { SidebarToggle } from "./SidebarToggle";

const paths = [
  "/",
  "/projects/$id",
  "/projects/$id/boards/$boardId",
  "/work-items/$id",
  "/functions/$id",
  "/articles/$id",
];

const entries: RecentEntry[] = [
  {
    type: "work-item",
    id: "w1",
    title: "Fix login",
    parent: "Kangaroo",
    to: "/work-items/$id",
    params: { id: "w1" },
  },
  {
    type: "board",
    id: "b1",
    title: "Sprint board",
    parent: "Kangaroo",
    to: "/projects/$id/boards/$boardId",
    params: { id: "p1", boardId: "b1" },
  },
  {
    type: "function",
    id: "f1",
    title: "Summarise",
    to: "/functions/$id",
    params: { id: "f1" },
  },
  {
    type: "article",
    id: "a1",
    title: "Onboarding guide",
    parent: "Team handbook",
    to: "/articles/$id",
    params: { id: "a1" },
  },
  {
    type: "project",
    id: "p1",
    title: "Kangaroo",
    to: "/projects/$id",
    params: { id: "p1" },
  },
];

test.beforeEach(async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.evaluate(() => localStorage.clear());
});

test.describe("Sidebar", () => {
  test("lists an entry of each type with the right link", async ({
    mount,
    page,
  }) => {
    await page.evaluate(
      (value) => localStorage.setItem("kangaroo-recent", JSON.stringify(value)),
      entries,
    );
    await mount(
      <SidebarProvider>
        <TestRouter paths={paths}>
          <Sidebar>
            <RecentSection />
          </Sidebar>
        </TestRouter>
      </SidebarProvider>,
    );
    const sidebar = page.getByRole("complementary", { name: "Sidebar" });
    await expect(
      sidebar.getByRole("link", { name: "Fix login" }),
    ).toHaveAttribute("href", "/work-items/w1");
    await expect(
      sidebar.getByRole("link", { name: "Sprint board" }),
    ).toHaveAttribute("href", "/projects/p1/boards/b1");
    await expect(
      sidebar.getByRole("link", { name: "Kangaroo", exact: true }),
    ).toHaveAttribute("href", "/projects/p1");
    await expect(
      sidebar.getByRole("link", { name: "Summarise" }),
    ).toHaveAttribute("href", "/functions/f1");
    await expect(
      sidebar.getByRole("link", { name: "Onboarding guide" }),
    ).toHaveAttribute("href", "/articles/a1");
  });

  test("shows the parent project or knowledge base under the title", async ({
    mount,
    page,
  }) => {
    await page.evaluate(
      (value) => localStorage.setItem("kangaroo-recent", JSON.stringify(value)),
      entries,
    );
    await mount(
      <SidebarProvider>
        <TestRouter paths={paths}>
          <Sidebar>
            <RecentSection />
          </Sidebar>
        </TestRouter>
      </SidebarProvider>,
    );
    const sidebar = page.getByRole("complementary", { name: "Sidebar" });
    await expect(
      sidebar.getByRole("link", { name: "Fix login" }),
    ).toContainText("Kangaroo");
    await expect(
      sidebar.getByRole("link", { name: "Onboarding guide" }),
    ).toContainText("Team handbook");
    await expect(
      sidebar.getByRole("link", { name: "Summarise" }),
    ).not.toContainText("Kangaroo");
  });

  test("shows the empty state", async ({ mount, page }) => {
    await mount(
      <SidebarProvider>
        <TestRouter paths={paths}>
          <Sidebar>
            <RecentSection />
          </Sidebar>
        </TestRouter>
      </SidebarProvider>,
    );
    await expect(page.getByText("Nothing yet")).toBeVisible();
  });

  test("minimised, shows only the clock and no entries", async ({
    mount,
    page,
  }) => {
    await page.evaluate(
      (value) => localStorage.setItem("kangaroo-recent", JSON.stringify(value)),
      entries,
    );
    await page.evaluate(() =>
      localStorage.setItem("kangaroo-sidebar", "collapsed"),
    );
    await mount(
      <SidebarProvider>
        <TestRouter paths={paths}>
          <Sidebar>
            <RecentSection />
          </Sidebar>
        </TestRouter>
      </SidebarProvider>,
    );
    const sidebar = page.getByRole("complementary", { name: "Sidebar" });
    await expect(sidebar).toHaveClass(/md:w-14/);
    await expect(sidebar.getByRole("button", { name: "Recent" })).toBeVisible();
    await expect(sidebar.getByRole("link", { name: "Fix login" })).toBeHidden();
    await expect(sidebar.getByRole("button", { name: "Recent" })).toBeVisible();
  });

  test("clicking the minimised clock expands the sidebar with Recent open", async ({
    mount,
    page,
  }) => {
    await page.evaluate(
      (value) => localStorage.setItem("kangaroo-recent", JSON.stringify(value)),
      entries,
    );
    await page.evaluate(() =>
      localStorage.setItem("kangaroo-sidebar", "collapsed"),
    );
    await mount(
      <SidebarProvider>
        <TestRouter paths={paths}>
          <Sidebar>
            <RecentSection />
          </Sidebar>
        </TestRouter>
      </SidebarProvider>,
    );
    const sidebar = page.getByRole("complementary", { name: "Sidebar" });
    await sidebar.getByRole("button", { name: "Recent" }).first().click();
    await expect(sidebar).toHaveClass(/md:w-56/);
    await expect(
      sidebar.getByRole("link", { name: "Fix login" }),
    ).toBeVisible();
    expect(
      await page.evaluate(() => localStorage.getItem("kangaroo-sidebar")),
    ).toBeNull();
  });

  test("the Recent heading opens and closes the list and remembers it", async ({
    mount,
    page,
  }) => {
    await page.evaluate(
      (value) => localStorage.setItem("kangaroo-recent", JSON.stringify(value)),
      entries,
    );
    await mount(
      <SidebarProvider>
        <TestRouter paths={paths}>
          <Sidebar>
            <RecentSection />
          </Sidebar>
        </TestRouter>
      </SidebarProvider>,
    );
    const sidebar = page.getByRole("complementary", { name: "Sidebar" });
    const heading = sidebar.getByRole("button", {
      name: "Recent",
      expanded: true,
    });
    await expect(
      sidebar.getByRole("link", { name: "Fix login" }),
    ).toBeVisible();
    await heading.click();
    await expect(
      sidebar.getByRole("button", { name: "Recent", expanded: false }),
    ).toBeVisible();
    await expect(sidebar.getByRole("link", { name: "Fix login" })).toBeHidden();
    expect(
      await page.evaluate(() =>
        localStorage.getItem("kangaroo-sidebar-recent"),
      ),
    ).toBe("closed");
  });

  test("collapses to the clock and remembers the choice", async ({
    mount,
    page,
  }) => {
    await page.evaluate(
      (value) => localStorage.setItem("kangaroo-recent", JSON.stringify(value)),
      entries,
    );
    await mount(
      <SidebarProvider>
        <TestRouter paths={paths}>
          <Sidebar>
            <RecentSection />
          </Sidebar>
        </TestRouter>
      </SidebarProvider>,
    );
    const sidebar = page.getByRole("complementary", { name: "Sidebar" });
    const collapse = sidebar.getByRole("button", { name: "Collapse sidebar" });
    await expect(collapse).toHaveAttribute("aria-expanded", "true");
    await collapse.click();
    await expect(
      sidebar.getByRole("button", { name: "Expand sidebar" }),
    ).toHaveAttribute("aria-expanded", "false");
    await expect(sidebar).toHaveClass(/md:w-14/);
    expect(
      await page.evaluate(() => localStorage.getItem("kangaroo-sidebar")),
    ).toBe("collapsed");
  });

  test("the mobile drawer opens and closes", async ({ mount, page }) => {
    await page.setViewportSize({ width: 390, height: 800 });
    await page.evaluate(
      (value) => localStorage.setItem("kangaroo-recent", JSON.stringify(value)),
      entries,
    );
    await mount(
      <SidebarProvider>
        <TestRouter paths={paths}>
          <SidebarToggle />
          <Sidebar>
            <RecentSection />
          </Sidebar>
        </TestRouter>
      </SidebarProvider>,
    );
    const sidebar = page.getByRole("complementary", { name: "Sidebar" });
    await expect(sidebar).toBeHidden();

    await page.getByRole("button", { name: "Open sidebar" }).click();
    await expect(sidebar).toBeVisible();

    await page.getByRole("link", { name: "Kangaroo", exact: true }).click();
    await expect(sidebar).toBeHidden();
  });
});
