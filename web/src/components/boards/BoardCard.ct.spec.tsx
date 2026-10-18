import { expect, test } from "../../../playwright/fixtures.ts";
import type { WorkItem } from "../../lib/work-items";
import { BoardCard } from "./BoardCard";
import { TestRouter } from "../TestRouter.story";

const paths = ["/", "/work-items/$id"];

const task: WorkItem = {
  id: "3f2a9c1d-0000-4000-8000-000000000001",
  title: "Fast trip search",
  description: null,
  rendered_description: null,
  project_id: "p1",
  status_id: "s-prog",
  type_id: "t-task",
  parent_id: null,
  status: { id: "s-prog", name: "In progress", category: "in_progress" },
  created_at: "2026-01-01T00:00:00Z",
  modified_at: "2026-01-01T00:00:00Z",
  labels: [],
  trashed: false,
  type: { id: "t-task", name: "Task", level: "standard" },
};

const subtask: WorkItem = {
  ...task,
  id: "7b8e4f2a-0000-4000-8000-000000000002",
  title: "Write migration",
  type_id: "t-sub",
  type: { id: "t-sub", name: "Subtask", level: "subtask" },
  parent_id: "3f2a9c1d-0000-4000-8000-000000000001",
};

const currentUser = {
  username: "test-user",
  email: "test@example.com",
  avatar_url: "https://gravatar.com/avatar/test?d=identicon&s=64",
};

test.beforeEach(async ({ page }) => {
  await page.route("**/api/v1/user", (route) =>
    route.fulfill({ json: currentUser }),
  );
});

test.describe("BoardCard", () => {
  test("renders the whole card as a link to the work item", async ({
    mount,
  }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <BoardCard item={task} />
      </TestRouter>,
    );
    await expect(component).toHaveAttribute("href", `/work-items/${task.id}`);
    await expect(component).toContainText("Fast trip search");
  });

  test("shows the type at the top and the full id in the footer", async ({
    mount,
  }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <BoardCard item={task} />
      </TestRouter>,
    );
    await expect(
      component.getByRole("img", { name: "Task", exact: true }),
    ).toBeAttached();
    await expect(component.getByText(task.id, { exact: true })).toBeVisible();
  });

  test("shows the labels above the id", async ({ mount }) => {
    const labeled = { ...task, labels: ["news", "sport"] };
    const component = await mount(
      <TestRouter paths={paths}>
        <BoardCard item={labeled} />
      </TestRouter>,
    );
    await expect(component.getByText("news", { exact: true })).toBeVisible();
    await expect(component.getByText("sport", { exact: true })).toBeVisible();

    const labelsBox = await component.locator("ul").boundingBox();
    const idBox = await component
      .getByText(task.id, { exact: true })
      .boundingBox();
    expect(labelsBox!.y + labelsBox!.height).toBeLessThanOrEqual(idBox!.y);
  });

  test("shows no labels row when the item has no labels", async ({ mount }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <BoardCard item={task} />
      </TestRouter>,
    );
    await expect(component.locator("ul")).toHaveCount(0);
  });

  test("labels a subtask with the subtask type", async ({ mount }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <BoardCard item={subtask} />
      </TestRouter>,
    );
    await expect(
      component.getByRole("img", { name: "Subtask", exact: true }),
    ).toBeAttached();
  });

  test("shows the logged-in user's Gravatar in the footer", async ({
    mount,
  }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <BoardCard item={task} />
      </TestRouter>,
    );
    await expect(
      component.getByRole("img", { name: currentUser.username, exact: true }),
    ).toHaveAttribute("src", currentUser.avatar_url);
  });
});
