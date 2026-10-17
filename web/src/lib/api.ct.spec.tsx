import { expect, test } from "../../playwright/fixtures.ts";
import { AppHeader } from "../components/app-header/AppHeader";
import { TestRouter } from "../components/TestRouter.story";

const paths = ["/", "/projects", "/work-items", "/about", "/admin"];

test.describe("apiFetch when logged out", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/api/v1/user", (route) =>
      route.fulfill({ status: 401, json: { detail: "Not authenticated" } }),
    );
  });

  test("sends the user to login", async ({ mount, page }) => {
    const logins: string[] = [];
    await page.route("**/login**", (route) => {
      logins.push(route.request().url());
      return route.fulfill({ body: "" });
    });

    await mount(
      <TestRouter paths={paths}>
        <AppHeader />
      </TestRouter>,
    );
    await expect.poll(() => logins.length).toBe(1);
    expect(logins[0]).toContain("/login?next=");
  });

  test("does not loop back to login right after a login", async ({
    mount,
    page,
  }) => {
    const logins: string[] = [];
    await page.route("**/login**", (route) => {
      logins.push(route.request().url());
      return route.fulfill({ body: "" });
    });
    await page.unroute("**/api/v1/user");
    await page.route("**/api/v1/user", async (route) => {
      await page.evaluate(() =>
        sessionStorage.setItem("login-redirected-at", String(Date.now())),
      );
      return route.fulfill({
        status: 401,
        json: { detail: "Not authenticated" },
      });
    });

    const userRequest = page.waitForResponse("**/api/v1/user");
    await mount(
      <TestRouter paths={paths}>
        <AppHeader />
      </TestRouter>,
    );
    await userRequest;
    await page.waitForTimeout(200);
    expect(logins).toEqual([]);
  });
});
