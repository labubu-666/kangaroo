import { expect, test } from "../../../playwright/fixtures.ts";
import { StatusBadge } from "./StatusBadge";

test.describe("StatusBadge", () => {
  test("renders the label and colour for each status", async ({ mount }) => {
    const component = await mount(
      <div>
        <StatusBadge
          status={{ id: "s-open", name: "Open", category: "todo" }}
        />
        <StatusBadge
          status={{
            id: "s-prog",
            name: "In progress",
            category: "in_progress",
          }}
        />
        <StatusBadge
          status={{ id: "s-done", name: "Done", category: "done" }}
        />
      </div>,
    );

    await expect(component.getByText("Open", { exact: true })).toHaveClass(
      /bg-yellow-100 dark:bg-yellow-900\/40 text-yellow-800 dark:text-yellow-200/,
    );
    await expect(
      component.getByText("In progress", { exact: true }),
    ).toHaveClass(
      /bg-blue-100 dark:bg-blue-900\/40 text-blue-800 dark:text-blue-200/,
    );
    await expect(component.getByText("Done", { exact: true })).toHaveClass(
      /bg-green-100 dark:bg-green-900\/40 text-green-800 dark:text-green-200/,
    );
  });
});
