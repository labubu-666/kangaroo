import { expect, test } from "../../../playwright/fixtures.ts";
import { TestRouter } from "../TestRouter.story";
import { ProfileDetails } from "./ProfileDetails";

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

test.describe("ProfileDetails", () => {
  test("shows username and email", async ({ mount }) => {
    const component = await mount(
      <TestRouter paths={["/profile"]}>
        <ProfileDetails />
      </TestRouter>,
    );
    await expect(
      component.getByText("test-user", { exact: true }),
    ).toBeVisible();
    await expect(component.getByText("test@example.com")).toBeVisible();
  });

  test("links to the API keys page", async ({ mount }) => {
    const component = await mount(
      <TestRouter paths={["/profile"]}>
        <ProfileDetails />
      </TestRouter>,
    );
    await expect(
      component.getByRole("link", { name: /Manage API keys/ }),
    ).toHaveAttribute("href", "/profile/api-keys");
  });
});
