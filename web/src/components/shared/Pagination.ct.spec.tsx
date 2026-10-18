import { expect, test } from "../../../playwright/fixtures.ts";
import { PaginationHarness } from "./PaginationHarness.story";

test.describe("Pagination", () => {
  test("shows Previous 1 Next when everything fits on one page", async ({
    mount,
    page,
  }) => {
    const component = await mount(<PaginationHarness total={10} limit={10} />);
    await expect(component.locator("ul button")).toHaveText(["1"]);
    await expect(
      component.getByRole("button", { name: "1", exact: true }),
    ).toHaveAttribute("aria-current", "page");
    await expect(page.getByRole("button", { name: "Previous" })).toBeDisabled();
    await expect(page.getByRole("button", { name: "Next" })).toBeDisabled();
  });

  test("starts on page 1 with Previous disabled", async ({ mount, page }) => {
    const component = await mount(<PaginationHarness total={30} limit={10} />);
    await expect(
      component.getByRole("button", { name: "1", exact: true }),
    ).toHaveAttribute("aria-current", "page");
    await expect(page.getByRole("button", { name: "Previous" })).toBeDisabled();
    await expect(page.getByRole("button", { name: "Next" })).toBeEnabled();
  });

  test("jumps to a numbered page", async ({ mount, page }) => {
    const component = await mount(<PaginationHarness total={50} limit={10} />);
    await page.getByRole("button", { name: "3", exact: true }).click();

    await expect(component.getByTestId("offset")).toHaveText("20");
    await expect(
      page.getByRole("button", { name: "3", exact: true }),
    ).toHaveAttribute("aria-current", "page");
    await expect(
      page.getByRole("button", { name: "1", exact: true }),
    ).not.toHaveAttribute("aria-current", "page");
  });

  test("Next and Previous move one page at a time", async ({ mount, page }) => {
    const component = await mount(<PaginationHarness total={30} limit={10} />);
    await page.getByRole("button", { name: "Next" }).click();
    await expect(component.getByTestId("offset")).toHaveText("10");

    await page.getByRole("button", { name: "Previous" }).click();
    await expect(component.getByTestId("offset")).toHaveText("0");
  });

  test("disables Next on the last page", async ({ mount, page }) => {
    await mount(<PaginationHarness total={30} limit={10} />);
    await page.getByRole("button", { name: "3", exact: true }).click();
    await expect(page.getByRole("button", { name: "Next" })).toBeDisabled();
  });

  test("shows at most 10 page numbers around the current page", async ({
    mount,
    page,
  }) => {
    const component = await mount(<PaginationHarness total={200} limit={10} />);
    const pageButtons = component.locator("ul button");
    await expect(pageButtons).toHaveCount(10);
    await expect(pageButtons.first()).toHaveText("1");
    await expect(pageButtons.last()).toHaveText("10");

    await page.getByRole("button", { name: "10", exact: true }).click();
    await expect(pageButtons.first()).toHaveText("6");
    await expect(pageButtons.last()).toHaveText("15");
  });
});
