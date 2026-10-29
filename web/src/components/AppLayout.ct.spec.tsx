import { expect, test } from "../../playwright/fixtures.ts";
import { AppHeader } from "./app-header/AppHeader";
import { PageBreadcrumbs } from "./breadcrumbs/BreadcrumbsContext";
import { RecentSection } from "./sidebar/RecentSection";
import { Sidebar } from "./sidebar/Sidebar";
import { SidebarProvider } from "./sidebar/SidebarContext";
import { SectionNav } from "./SectionNav";
import { TestRouter } from "./TestRouter.story";

test.beforeEach(async ({ page }) => {
  await page.route("**/api/v1/user", (route) =>
    route.fulfill({
      json: {
        username: "test-user",
        email: "test@example.com",
        avatar_url: "https://gravatar.com/avatar/test?d=identicon&s=64",
      },
    }),
  );
});

test.describe("App layout", () => {
  test("renders the section links above the breadcrumbs", async ({
    mount,
    page,
  }) => {
    await mount(
      <TestRouter
        breadcrumbs={[{ label: "Projects", to: "/projects" }, { label: "New" }]}
      >
        <AppHeader />
        <SectionNav />
        <PageBreadcrumbs />
      </TestRouter>,
    );
    const breadcrumbs = page.getByRole("navigation", { name: "Breadcrumb" });
    const sections = page.getByRole("navigation", { name: "Sections" });
    await expect(breadcrumbs).toBeVisible();
    await expect(sections).toBeVisible();
    const breadcrumbsBox = await breadcrumbs.boundingBox();
    const sectionsBox = await sections.boundingBox();
    expect(sectionsBox!.y).toBeLessThan(breadcrumbsBox!.y);
  });

  test("places the recent sidebar to the left of the content", async ({
    mount,
    page,
  }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await mount(
      <SidebarProvider>
        <TestRouter breadcrumbs={[{ label: "Projects" }]}>
          <div className="flex">
            <Sidebar>
              <RecentSection />
            </Sidebar>
            <div className="flex-1">
              <PageBreadcrumbs />
            </div>
          </div>
        </TestRouter>
      </SidebarProvider>,
    );
    const sidebar = page.getByRole("complementary", { name: "Sidebar" });
    const breadcrumbs = page.getByRole("navigation", { name: "Breadcrumb" });
    const sidebarBox = await sidebar.boundingBox();
    const breadcrumbsBox = await breadcrumbs.boundingBox();
    expect(sidebarBox!.x + sidebarBox!.width).toBeLessThanOrEqual(
      breadcrumbsBox!.x,
    );
  });

  test("omits the breadcrumbs when the page publishes none", async ({
    mount,
    page,
  }) => {
    await mount(
      <TestRouter breadcrumbs={[]}>
        <AppHeader />
        <SectionNav />
        <PageBreadcrumbs />
      </TestRouter>,
    );
    await expect(
      page.getByRole("navigation", { name: "Sections" }),
    ).toBeVisible();
    await expect(
      page.getByRole("navigation", { name: "Breadcrumb" }),
    ).toHaveCount(0);
  });
});
