import { expect, test } from "../../../playwright/fixtures.ts";
import { AppHeader } from "./AppHeader";
import { TestRouter } from "../TestRouter.story";

const paths = ["/", "/projects", "/work-items", "/about", "/admin"];

const currentUser = {
  username: "test-user",
  email: "test@example.com",
  avatar_url: "https://gravatar.com/avatar/test?d=identicon&s=64",
};

test.beforeEach(async ({ page }) => {
  await page.route("**/api/v1/user", (route) =>
    route.fulfill({ json: currentUser }),
  );
});

test.describe("AppHeader", () => {
  test("shows the Gravatar as the profile avatar", async ({ mount, page }) => {
    await mount(
      <TestRouter paths={paths}>
        <AppHeader />
      </TestRouter>,
    );
    await expect(
      page.getByRole("button", { name: "Profile menu" }).locator("img"),
    ).toHaveAttribute("src", currentUser.avatar_url);
  });

  test("shows username and email in the profile menu", async ({ mount }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <AppHeader />
      </TestRouter>,
    );
    await component.getByRole("button", { name: "Profile menu" }).click();
    const menu = component.getByRole("menu");
    await expect(menu.getByText("test-user", { exact: true })).toBeVisible();
    await expect(menu.getByText("test@example.com")).toBeVisible();
  });

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

  test("logs out with a POST form in the profile menu", async ({ mount }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <AppHeader />
      </TestRouter>,
    );
    await component.getByRole("button", { name: "Profile menu" }).click();
    await expect(
      component
        .locator('form[method="post"][action="/auth/logout"]')
        .getByRole("menuitem", { name: "Logout" }),
    ).toBeVisible();
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
