import { expect, test } from "../../playwright/fixtures.ts";
import { AppHeader } from "./app-header/AppHeader";
import { PageBreadcrumbs } from "./breadcrumbs/BreadcrumbsContext";
import { SectionNav } from "./SectionNav";
import { TestRouter } from "./TestRouter.story";

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
