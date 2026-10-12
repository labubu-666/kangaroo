import { expect, test } from "../../../playwright/fixtures.ts";
import { CopyFilter } from "./CopyFilter";

test.describe("CopyFilter", () => {
  test("copies the filter and shows feedback", async ({
    mount,
    page,
    context,
  }) => {
    await context.grantPermissions(["clipboard-read", "clipboard-write"]);
    const filter = "labels contains 'derstandard' and status != 'done'";
    const component = await mount(<CopyFilter filter={filter} />);

    const button = page.getByRole("button", { name: "Copy filter" });
    await expect(button).toHaveClass(/font-mono/);

    await button.click();

    await expect(component.getByText("Copied!")).toBeVisible();
    const clipboard = await page.evaluate(() => navigator.clipboard.readText());
    expect(clipboard).toBe(filter);
  });
});
