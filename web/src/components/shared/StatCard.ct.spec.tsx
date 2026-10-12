import { expect, test } from "../../../playwright/fixtures.ts";
import { StatCard } from "./StatCard";
import { TestRouter } from "../TestRouter.story";

const paths = ["/", "/projects", "/work-items"];

test.describe("StatCard", () => {
  test("shows the label and value", async ({ mount }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <StatCard label="Projects" value={3} />
      </TestRouter>,
    );
    await expect(
      component.getByText("Projects", { exact: true }),
    ).toBeVisible();
    await expect(component.getByText("3", { exact: true })).toBeVisible();
  });

  test("links to the list page when a target is given", async ({ mount }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <StatCard label="Work items" value={7} to="/work-items" />
      </TestRouter>,
    );
    await expect(component).toHaveAttribute("href", "/work-items");
    await expect(component).toContainText("Work items");
  });

  test("passes the search to the link", async ({ mount }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <StatCard
          label="In progress"
          value={2}
          to="/work-items"
          search={{ filter: "status == 'in_progress'" }}
        />
      </TestRouter>,
    );
    await expect(component).toHaveAttribute(
      "href",
      "/work-items?filter=status+%3D%3D+%27in_progress%27",
    );
  });
});
