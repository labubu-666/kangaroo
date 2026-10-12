import { expect, test } from "../../../playwright/fixtures.ts";
import { AppHeader } from "./AppHeader";
import { TestRouter } from "../TestRouter.story";

const paths = ["/", "/projects", "/work-items", "/about", "/admin"];

test.describe("AppHeader", () => {
  test("renders a navigation landmark", async ({ mount, page }) => {
    await mount(
      <TestRouter paths={paths}>
        <AppHeader />
      </TestRouter>,
    );
    // mount() returns the router root, so query the page for the landmark.
    await expect(page.getByRole("navigation")).toBeVisible();
  });

  test("hides about and admin links until the profile menu is opened", async ({
    mount,
  }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <AppHeader />
      </TestRouter>,
    );
    await expect(component.getByRole("link", { name: "About" })).toHaveCount(0);
    await expect(component.getByRole("link", { name: "Admin" })).toHaveCount(0);
    await component.getByRole("button", { name: "Profile menu" }).click();
    await expect(component.getByRole("menu")).toBeVisible();
  });

  test("renders a link to about in the profile menu", async ({ mount }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <AppHeader />
      </TestRouter>,
    );
    await component.getByRole("button", { name: "Profile menu" }).click();
    await expect(
      component.getByRole("menuitem", { name: "About" }),
    ).toHaveAttribute("href", "/about");
  });

  test("renders a link to admin in the profile menu", async ({ mount }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <AppHeader />
      </TestRouter>,
    );
    await component.getByRole("button", { name: "Profile menu" }).click();
    await expect(
      component.getByRole("menuitem", { name: "Admin" }),
    ).toHaveAttribute("href", "/admin");
  });

  test("renders a kangaroo home link", async ({ mount }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <AppHeader />
      </TestRouter>,
    );
    const home = component.getByRole("link", { name: "Home" });
    await expect(home).toHaveAttribute("href", "/");
    await expect(home).toHaveText("🦘");
  });

  test("highlights the about link for the current route", async ({ mount }) => {
    const component = await mount(
      <TestRouter paths={paths} initialPath="/about">
        <AppHeader />
      </TestRouter>,
    );
    await component.getByRole("button", { name: "Profile menu" }).click();
    await expect(
      component.getByRole("menuitem", { name: "About" }),
    ).toHaveClass(/text-blue-600/);
    await expect(component.getByRole("link", { name: "Home" })).not.toHaveClass(
      /text-blue-600/,
    );
  });
});
