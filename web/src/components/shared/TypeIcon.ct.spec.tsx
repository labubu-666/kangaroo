import { expect, test } from "../../../playwright/fixtures.ts";
import { TypeIcon } from "./TypeIcon";

test.describe("TypeIcon", () => {
  test("labels the icon with the type name", async ({ mount }) => {
    const component = await mount(
      <div>
        <TypeIcon type={{ id: "t-bug", name: "Bug" }} />
      </div>,
    );
    await expect(
      component.getByRole("img", { name: "Bug", exact: true }),
    ).toBeAttached();
  });

  test("uses a different fill for each known type", async ({ mount }) => {
    const component = await mount(
      <div>
        <TypeIcon type={{ id: "t-story", name: "Story" }} />
        <TypeIcon type={{ id: "t-bug", name: "Bug" }} />
        <TypeIcon type={{ id: "t-task", name: "Task" }} />
      </div>,
    );
    await expect(
      component.getByRole("img", { name: "Story" }).locator("rect").first(),
    ).toHaveAttribute("fill", "#36B37E");
    await expect(
      component.getByRole("img", { name: "Bug" }).locator("rect").first(),
    ).toHaveAttribute("fill", "#E5493A");
    await expect(
      component.getByRole("img", { name: "Task" }).locator("rect").first(),
    ).toHaveAttribute("fill", "#4BADE8");
  });

  test("falls back to the task icon for an unknown type", async ({ mount }) => {
    const component = await mount(
      <div>
        <TypeIcon type={{ id: "t-x", name: "Epic" }} />
      </div>,
    );
    await expect(
      component.getByRole("img", { name: "Epic" }).locator("rect").first(),
    ).toHaveAttribute("fill", "#4BADE8");
  });
});
