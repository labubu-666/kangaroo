import { expect, test } from "../../../playwright/fixtures.ts";
import { TypeBadge } from "./TypeBadge";

test.describe("TypeBadge", () => {
  test("colours stories green, bugs red and tasks blue", async ({ mount }) => {
    const component = await mount(
      <div>
        <TypeBadge type={{ id: "t-task", name: "Task" }} />
        <TypeBadge type={{ id: "t-bug", name: "Bug" }} />
        <TypeBadge type={{ id: "t-story", name: "Story" }} />
      </div>,
    );

    await expect(component.getByText("Task", { exact: true })).toHaveClass(
      /bg-primary-subtle text-primary/,
    );
    await expect(component.getByText("Bug", { exact: true })).toHaveClass(
      /bg-red-100 text-red-800/,
    );
    await expect(component.getByText("Story", { exact: true })).toHaveClass(
      /bg-green-100 text-green-800/,
    );
  });
});
