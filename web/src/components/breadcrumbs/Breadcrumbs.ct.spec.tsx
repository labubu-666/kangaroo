import { expect, test } from "../../../playwright/fixtures.ts";
import { Breadcrumbs } from "./Breadcrumbs";
import { TestRouter } from "../TestRouter.story";

const paths = ["/", "/projects", "/projects/$id"];

test.describe("Breadcrumbs", () => {
  test("renders a labelled breadcrumb navigation landmark", async ({
    mount,
    page,
  }) => {
    await mount(
      <TestRouter paths={paths}>
        <Breadcrumbs
          items={[{ label: "Projects", to: "/projects" }, { label: "New" }]}
        />
      </TestRouter>,
    );
    // mount() returns the <nav> root itself, so query the page for the landmark.
    await expect(
      page.getByRole("navigation", { name: "Breadcrumb" }),
    ).toBeVisible();
  });

  test("renders linked items for non-last entries with a link", async ({
    mount,
  }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <Breadcrumbs
          items={[{ label: "Projects", to: "/projects" }, { label: "New" }]}
        />
      </TestRouter>,
    );
    const link = component.getByRole("link", { name: "Projects" });
    await expect(link).toBeVisible();
    await expect(link).toHaveAttribute("href", "/projects");
  });

  test("renders the last item as the current page without a link", async ({
    mount,
  }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <Breadcrumbs
          items={[{ label: "Projects", to: "/projects" }, { label: "New" }]}
        />
      </TestRouter>,
    );
    const current = component.getByText("New", { exact: true });
    await expect(current).toHaveAttribute("aria-current", "page");
    await expect(component.getByRole("link", { name: "New" })).toHaveCount(0);
  });

  test("renders a non-last item without a target as plain text", async ({
    mount,
  }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <Breadcrumbs items={[{ label: "Work items" }, { label: "Detail" }]} />
      </TestRouter>,
    );
    const plain = component.getByText("Work items", { exact: true });
    await expect(plain).toBeVisible();
    await expect(plain).not.toHaveAttribute("aria-current");
    await expect(
      component.getByRole("link", { name: "Work items" }),
    ).toHaveCount(0);
  });

  test("applies search params to a linked item", async ({ mount }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <Breadcrumbs
          items={[
            {
              label: "Work items",
              to: "/work-items",
              search: { filter: "project.id == 'abc'" },
            },
            { label: "Detail" },
          ]}
        />
      </TestRouter>,
    );
    const link = component.getByRole("link", { name: "Work items" });
    await expect(link).toHaveAttribute(
      "href",
      "/work-items?filter=project.id+%3D%3D+%27abc%27",
    );
  });

  test("renders a separator between items but not before the first", async ({
    mount,
  }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <Breadcrumbs
          items={[
            { label: "Projects", to: "/projects" },
            { label: "Project A", to: "/projects/1" },
            { label: "Edit" },
          ]}
        />
      </TestRouter>,
    );
    await expect(component.locator("li")).toHaveCount(4);
    await expect(
      component.locator("li").nth(0).locator('span[aria-hidden="true"]'),
    ).toHaveCount(0);
    await expect(
      component.locator("li").nth(1).locator('span[aria-hidden="true"]'),
    ).toHaveText("/");
    await expect(
      component.locator("li").nth(2).locator('span[aria-hidden="true"]'),
    ).toHaveText("/");
    await expect(
      component.locator("li").nth(3).locator('span[aria-hidden="true"]'),
    ).toHaveText("/");
  });

  test("renders Home as the first entry linking to the root", async ({
    mount,
  }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <Breadcrumbs
          items={[{ label: "Projects", to: "/projects" }, { label: "New" }]}
        />
      </TestRouter>,
    );
    const home = component.getByRole("link", { name: "Home" });
    await expect(home).toBeVisible();
    await expect(home).toHaveAttribute("href", "/");
    await expect(component.locator("li").nth(0)).toContainText("Home");
  });

  test("renders only the current Home item on the home page", async ({
    mount,
  }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <Breadcrumbs items={[{ label: "Home", to: "/" }]} />
      </TestRouter>,
    );
    await expect(component.locator("li")).toHaveCount(1);
    await expect(component.locator("li").nth(0)).toHaveText("Home");
    await expect(component.getByRole("link", { name: "Home" })).toHaveCount(0);
    await expect(component.locator('[aria-current="page"]')).toHaveText("Home");
  });
});
