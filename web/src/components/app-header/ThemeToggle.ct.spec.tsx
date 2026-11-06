import { expect, test } from "../../../playwright/fixtures.ts";
import { ThemeToggle } from "./ThemeToggle";

test.describe("ThemeToggle", () => {
  test("the System theme follows the OS setting as it changes", async ({
    mount,
    page,
  }) => {
    await page.emulateMedia({ colorScheme: "light" });
    await mount(<ThemeToggle />);
    const html = page.locator("html");

    await page.emulateMedia({ colorScheme: "dark" });
    await expect(html).toHaveClass(/\bdark\b/);

    await page.emulateMedia({ colorScheme: "light" });
    await expect(html).not.toHaveClass(/\bdark\b/);
  });
});
