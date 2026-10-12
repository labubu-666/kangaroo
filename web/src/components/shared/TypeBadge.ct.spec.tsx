import { expect, test } from "../../../playwright/fixtures.ts";
import { TypeBadge } from "./TypeBadge";

test.describe("TypeBadge", () => {
  test("renders the label and colour for each type", async ({ mount }) => {
    const component = await mount(
      <div>
        <TypeBadge type={{ id: "t-task", name: "Task", level: "standard" }} />
        <TypeBadge type={{ id: "t-sub", name: "Subtask", level: "subtask" }} />
      </div>,
    );

    await expect(component.getByText("Task", { exact: true })).toHaveClass(
      /bg-gray-100 text-gray-800/,
    );
    await expect(component.getByText("Subtask", { exact: true })).toHaveClass(
      /bg-purple-100 text-purple-800/,
    );
  });
});
