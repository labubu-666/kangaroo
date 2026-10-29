import { expect, test } from "../../../playwright/fixtures.ts";
import { TypeBadge } from "./TypeBadge";

test.describe("TypeBadge", () => {
  test("renders the type name with the same colour for every type", async ({
    mount,
  }) => {
    const component = await mount(
      <div>
        <TypeBadge type={{ id: "t-task", name: "Task" }} />
        <TypeBadge type={{ id: "t-bug", name: "Bug" }} />
      </div>,
    );

    await expect(component.getByText("Task", { exact: true })).toHaveClass(
      /rounded bg-surface-strong px-2 py-0.5 text-xs font-medium text-fg/,
    );
    await expect(component.getByText("Bug", { exact: true })).toHaveClass(
      /rounded bg-surface-strong px-2 py-0.5 text-xs font-medium text-fg/,
    );
  });
});
