import { expect, test } from "../../../playwright/fixtures.ts";
import { ConfirmChange } from "./ConfirmChange";

test.describe("ConfirmChange", () => {
  test("lists every line that the change affects", async ({ mount }) => {
    const component = await mount(
      <ConfirmChange
        title="Rename status “Open”?"
        lines={[
          "Renaming stops these saved board filters from matching:",
          "Board “Open work” uses status == 'Open'",
        ]}
        busy={false}
        onConfirm={() => {}}
        onCancel={() => {}}
      />,
    );
    await expect(component).toContainText("Rename status “Open”?");
    await expect(component).toContainText(
      "Board “Open work” uses status == 'Open'",
    );
  });

  test("continue and cancel each call their handler", async ({ mount }) => {
    const calls: string[] = [];
    const component = await mount(
      <ConfirmChange
        title="Change the category?"
        lines={["3 work items will change from To do to Done."]}
        busy={false}
        onConfirm={() => calls.push("confirm")}
        onCancel={() => calls.push("cancel")}
      />,
    );
    await component.getByRole("button", { name: "Continue" }).click();
    await component.getByRole("button", { name: "Cancel" }).click();
    expect(calls).toEqual(["confirm", "cancel"]);
  });
});
