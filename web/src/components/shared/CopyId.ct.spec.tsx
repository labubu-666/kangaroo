import { expect, test } from "../../../playwright/fixtures.ts";
import { CopyId } from "./CopyId";

test.describe("CopyId", () => {
  test("copies the url and shows feedback", async ({
    mount,
    page,
    context,
  }) => {
    await context.grantPermissions(["clipboard-read", "clipboard-write"]);
    const url = "http://localhost/work-items/abc123";
    const component = await mount(<CopyId id="abc123" url={url} />);

    const button = page.getByRole("button", { name: "Copy link for abc123" });
    await expect(button).toHaveClass(/font-mono/);
    await expect(button).toHaveClass(/bg-gray-100/);

    await button.click();

    await expect(component.getByText("Copied!")).toBeVisible();
    const clipboard = await page.evaluate(() => navigator.clipboard.readText());
    expect(clipboard).toBe(url);
  });
});
