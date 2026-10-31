import { expect, test } from "../../playwright/fixtures.ts";
import { InlineEdit } from "./InlineEdit";
import { TestRouter } from "./TestRouter.story";

test.describe("InlineEdit", () => {
  test("opens the editor when the content is clicked", async ({
    mount,
    page,
  }) => {
    await mount(
      <TestRouter>
        <InlineEdit
          value="text"
          onSave={async () => {}}
          ariaLabel="description"
        >
          <p>text</p>
        </InlineEdit>
      </TestRouter>,
    );

    await page.getByRole("button", { name: "Edit description" }).click();

    await expect(
      page.getByRole("textbox", { name: "description" }),
    ).toBeVisible();
  });

  test("opens a CodeMirror editor when language is markdown", async ({
    mount,
    page,
  }) => {
    await mount(
      <TestRouter>
        <InlineEdit
          value="# Title"
          onSave={async () => {}}
          ariaLabel="description"
          language="markdown"
        >
          <p>Title</p>
        </InlineEdit>
      </TestRouter>,
    );

    await page.getByRole("button", { name: "Edit description" }).click();

    await expect(page.locator(".cm-editor")).toBeVisible();
    await expect(page.locator(".cm-content")).toContainText("# Title");
  });

  test("clicking a link inside the content does not open the editor", async ({
    mount,
    page,
  }) => {
    await mount(
      <TestRouter>
        <InlineEdit
          value="see link"
          onSave={async () => {}}
          ariaLabel="description"
        >
          <p>
            see <a href="#">link</a>
          </p>
        </InlineEdit>
      </TestRouter>,
    );

    await page.getByRole("link", { name: "link" }).click({ noWaitAfter: true });

    await expect(
      page.getByRole("textbox", { name: "description" }),
    ).toHaveCount(0);
    await expect(
      page.getByRole("button", { name: "Edit description" }),
    ).toBeVisible();
  });
});
