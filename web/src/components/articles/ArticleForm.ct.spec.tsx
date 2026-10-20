import { expect, test } from "../../../playwright/fixtures.ts";
import { TestRouter } from "../TestRouter.story";
import { ArticleForm, type ArticleFormValues } from "./ArticleForm";

const empty: ArticleFormValues = {
  title: "",
  body: "",
  labels: [],
};

const paths = ["/", "/knowledge-bases/$id", "/articles/$id"];

test.describe("ArticleForm", () => {
  test("shows the initial values", async ({ mount }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <ArticleForm
          initial={{
            title: "Setup",
            body: "# Setup",
            labels: ["howto"],
          }}
          submitLabel="Save"
          pendingLabel="Saving..."
          disabled={false}
          error={null}
          onCancel={() => {}}
          onSubmit={() => {}}
        />
      </TestRouter>,
    );
    await expect(component.getByLabel("Title *")).toHaveValue("Setup");
    await expect(component.getByLabel("Body", { exact: true })).toContainText(
      "# Setup",
    );
    await expect(component.getByText("howto", { exact: true })).toBeVisible();
  });

  test("requires a title and body before submitting", async ({ mount }) => {
    let submitted = false;
    const component = await mount(
      <TestRouter paths={paths}>
        <ArticleForm
          initial={empty}
          submitLabel="Create"
          pendingLabel="Creating..."
          disabled={false}
          error={null}
          onCancel={() => {}}
          onSubmit={() => {
            submitted = true;
          }}
        />
      </TestRouter>,
    );
    await component.getByRole("button", { name: "Create" }).click();
    await expect(component.getByText("Title is required")).toBeVisible();
    await expect(component.getByText("Body is required")).toBeVisible();
    expect(submitted).toBe(false);
  });

  test("Cancel calls onCancel instead of navigating", async ({ mount }) => {
    let cancelled = false;
    const component = await mount(
      <TestRouter paths={paths}>
        <ArticleForm
          initial={empty}
          submitLabel="Save"
          pendingLabel="Saving..."
          disabled={false}
          error={null}
          onCancel={() => {
            cancelled = true;
          }}
          onSubmit={() => {}}
        />
      </TestRouter>,
    );
    await component.getByRole("button", { name: "Cancel" }).click();
    expect(cancelled).toBe(true);
  });
});
