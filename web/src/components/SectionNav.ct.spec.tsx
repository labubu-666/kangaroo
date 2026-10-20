import { expect, test } from "../../playwright/fixtures.ts";
import { SectionNav } from "./SectionNav";
import { TestRouter } from "./TestRouter.story";

const paths = ["/", "/projects", "/work-items", "/functions", "/articles"];

test.describe("SectionNav", () => {
  test("renders a labelled navigation landmark", async ({ mount, page }) => {
    await mount(
      <TestRouter paths={paths}>
        <SectionNav />
      </TestRouter>,
    );
    // mount() returns the <nav> root itself, so query the page for the landmark.
    await expect(
      page.getByRole("navigation", { name: "Sections" }),
    ).toBeVisible();
  });

  test("renders links to home, projects, work items and functions only", async ({
    mount,
  }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <SectionNav />
      </TestRouter>,
    );
    await expect(component.getByRole("link", { name: "Home" })).toHaveAttribute(
      "href",
      "/",
    );
    await expect(
      component.getByRole("link", { name: "Projects" }),
    ).toHaveAttribute("href", "/projects");
    await expect(
      component.getByRole("link", { name: "Work items" }),
    ).toHaveAttribute("href", "/work-items");
    await expect(
      component.getByRole("link", { name: "Functions" }),
    ).toHaveAttribute("href", "/functions");
    await expect(
      component.getByRole("link", { name: "Knowledge base" }),
    ).toHaveAttribute("href", "/articles");
    await expect(component.getByRole("link", { name: "Boards" })).toHaveCount(
      0,
    );
  });

  test("highlights the link for the current route", async ({ mount }) => {
    const component = await mount(
      <TestRouter paths={paths} initialPath="/work-items">
        <SectionNav />
      </TestRouter>,
    );
    await expect(
      component.getByRole("link", { name: "Work items" }),
    ).toHaveClass(/text-blue-600/);
    await expect(
      component.getByRole("link", { name: "Projects" }),
    ).not.toHaveClass(/text-blue-600/);
  });

  test("highlights home only on the root route", async ({ mount }) => {
    const component = await mount(
      <TestRouter paths={paths} initialPath="/work-items">
        <SectionNav />
      </TestRouter>,
    );
    await expect(component.getByRole("link", { name: "Home" })).not.toHaveClass(
      /text-blue-600/,
    );
  });
});
