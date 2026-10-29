import { expect, test } from "../../playwright/fixtures.ts";
import { RecentRecorder } from "../components/sidebar/RecentRecorder.story";
import { RecentSection } from "../components/sidebar/RecentSection";
import { Sidebar } from "../components/sidebar/Sidebar";
import { SidebarProvider } from "../components/sidebar/SidebarContext";
import { TestRouter } from "../components/TestRouter.story";
import type { RecentEntry } from "./recent";

const paths = ["/", "/projects/$id", "/work-items/$id"];

function workItem(id: string): RecentEntry {
  return {
    type: "work-item",
    id,
    title: `Item ${id}`,
    parent: "Kangaroo",
    to: "/work-items/$id",
    params: { id },
  };
}

test.beforeEach(async ({ page }) => {
  await page.evaluate(() => localStorage.clear());
});

test.describe("recent entries", () => {
  test("puts the most recent entry first", async ({ mount, page }) => {
    await mount(
      <SidebarProvider>
        <TestRouter paths={paths}>
          <RecentRecorder entry={workItem("1")} />
          <RecentRecorder entry={workItem("2")} />
          <Sidebar>
            <RecentSection />
          </Sidebar>
        </TestRouter>
      </SidebarProvider>,
    );
    const titles = page.getByRole("complementary", { name: "Sidebar" });
    await expect(titles.locator("li")).toHaveCount(2);
    await expect(titles.locator("li").first()).toContainText("Item 2");
  });

  test("keeps only the 10 most recent entries", async ({ mount, page }) => {
    await mount(
      <SidebarProvider>
        <TestRouter paths={paths}>
          {Array.from({ length: 11 }, (_, i) => (
            <RecentRecorder key={i} entry={workItem(String(i + 1))} />
          ))}
          <Sidebar>
            <RecentSection />
          </Sidebar>
        </TestRouter>
      </SidebarProvider>,
    );
    const items = page
      .getByRole("complementary", { name: "Sidebar" })
      .locator("li");
    await expect(items).toHaveCount(10);
    await expect(items.first()).toContainText("Item 11");
    await expect(page.getByTitle("Item 1", { exact: true })).toHaveCount(0);
  });

  test("moves a revisited entry to the top without duplicating it", async ({
    mount,
    page,
  }) => {
    await mount(
      <SidebarProvider>
        <TestRouter paths={paths}>
          <RecentRecorder entry={workItem("1")} />
          <RecentRecorder entry={workItem("2")} />
          <RecentRecorder entry={workItem("1")} />
          <Sidebar>
            <RecentSection />
          </Sidebar>
        </TestRouter>
      </SidebarProvider>,
    );
    const items = page
      .getByRole("complementary", { name: "Sidebar" })
      .locator("li");
    await expect(items).toHaveCount(2);
    await expect(items.first()).toContainText("Item 1");
  });

  test("clear empties the list", async ({ mount, page }) => {
    await mount(
      <SidebarProvider>
        <TestRouter paths={paths}>
          <RecentRecorder entry={workItem("1")} />
          <Sidebar>
            <RecentSection />
          </Sidebar>
        </TestRouter>
      </SidebarProvider>,
    );
    await page
      .getByRole("complementary", { name: "Sidebar" })
      .getByRole("button", { name: "Clear" })
      .click();
    await expect(page.getByText("Nothing yet")).toBeVisible();
  });
});
