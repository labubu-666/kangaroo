import { expect, test } from "../../../playwright/fixtures.ts";
import { ReplacementDialog } from "./ReplacementDialog";

const options = [
  { id: "s-prog", name: "In Progress" },
  { id: "s-done", name: "Done" },
];

test.describe("ReplacementDialog", () => {
  test("names the item and how many work items use it", async ({ mount }) => {
    const component = await mount(
      <ReplacementDialog
        kind="status"
        name="Open"
        count={3}
        options={options}
        busy={false}
        error={null}
        onConfirm={() => {}}
        onCancel={() => {}}
      />,
    );
    await expect(component).toContainText("Delete status “Open”?");
    await expect(component).toContainText("3 work items use this status");
  });

  test("keeps delete disabled until a replacement is chosen", async ({
    mount,
  }) => {
    const component = await mount(
      <ReplacementDialog
        kind="status"
        name="Open"
        count={1}
        options={options}
        busy={false}
        error={null}
        onConfirm={() => {}}
        onCancel={() => {}}
      />,
    );
    const confirm = component.getByRole("button", {
      name: "Delete and move items",
    });
    await expect(confirm).toBeDisabled();
    await component.getByLabel("Replacement status").selectOption("s-done");
    await expect(confirm).toBeEnabled();
  });

  test("passes the chosen replacement to onConfirm", async ({ mount }) => {
    let chosen: string | null = null;
    const component = await mount(
      <ReplacementDialog
        kind="status"
        name="Open"
        count={1}
        options={options}
        busy={false}
        error={null}
        onConfirm={(id) => {
          chosen = id;
        }}
        onCancel={() => {}}
      />,
    );
    await component.getByLabel("Replacement status").selectOption("s-prog");
    await component
      .getByRole("button", { name: "Delete and move items" })
      .click();
    expect(chosen).toBe("s-prog");
  });

  test("shows the API error when the replacement is refused", async ({
    mount,
  }) => {
    const component = await mount(
      <ReplacementDialog
        kind="type"
        name="Task"
        count={2}
        options={options}
        busy={false}
        error="The replacement must be another type"
        onConfirm={() => {}}
        onCancel={() => {}}
      />,
    );
    await expect(component).toContainText(
      "The replacement must be another type",
    );
  });
});
