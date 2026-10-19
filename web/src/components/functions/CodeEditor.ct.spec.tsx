import { expect, test } from "../../../playwright/fixtures.ts";
import { CodeEditor } from "./CodeEditor";

test.describe("CodeEditor", () => {
  test("highlights Python keywords", async ({ mount, page }) => {
    await mount(<CodeEditor value="def hello():" ariaLabel="Code" readOnly />);
    const keyword = page.locator(".cm-line span", { hasText: "def" }).first();
    await expect(keyword).toHaveClass(/ͼ/);
  });

  test("shows line numbers and scrolls long code inside a capped height", async ({
    mount,
    page,
  }) => {
    const lines = Array.from({ length: 80 }, (_, i) => `print(${i})`);
    await mount(
      <CodeEditor value={lines.join("\n")} ariaLabel="Code" readOnly />,
    );
    await expect(page.locator(".cm-lineNumbers")).toBeVisible();
    const editor = page.locator(".cm-editor");
    const box = await editor.boundingBox();
    expect(box?.height).toBeLessThanOrEqual(24 * 16);
    const scroller = page.locator(".cm-scroller");
    await expect(scroller).toBeVisible();
  });

  test("fill mode limits the editor to the window and scrolls long code", async ({
    mount,
    page,
  }) => {
    await page.setViewportSize({ width: 800, height: 600 });
    const lines = Array.from({ length: 200 }, (_, i) => `print(${i})`);
    await mount(
      <CodeEditor value={lines.join("\n")} ariaLabel="Code" readOnly fill />,
    );
    const box = await page.locator(".cm-editor").boundingBox();
    expect(box?.height).toBeLessThan(600);
    const overflows = await page
      .locator(".cm-scroller")
      .evaluate((el) => el.scrollHeight > el.clientHeight);
    expect(overflows).toBe(true);
  });
});
