import { expect, test } from "../../playwright/fixtures.ts";
import { GoBackOrButton } from "../components/GoBackOrButton.story";
import { TestRouter } from "../components/TestRouter.story";

const paths = [
  "/projects/$id/boards/$boardId",
  "/work-items",
  "/work-items/$id",
  "/work-items/$id/edit",
];

const board = "/projects/p1/boards/b1";

test.describe("useGoBackOr", () => {
  test("falls back to the filtered work items list on a shared link", async ({
    mount,
  }) => {
    const component = await mount(
      <TestRouter paths={paths} initialEntries={["/work-items/1"]} showLocation>
        <GoBackOrButton label="Trash" target="list" projectId="p1" />
      </TestRouter>,
    );
    await component.getByRole("button", { name: "Trash" }).click();
    await expect(component.getByTestId("location")).toHaveText(
      "/work-items?filter=project.id+%3D%3D+%27p1%27",
    );
  });

  test("falls back to the unfiltered work items list when no project is known", async ({
    mount,
  }) => {
    const component = await mount(
      <TestRouter paths={paths} initialEntries={["/work-items/1"]} showLocation>
        <GoBackOrButton label="Trash" target="list" />
      </TestRouter>,
    );
    await component.getByRole("button", { name: "Trash" }).click();
    await expect(component.getByTestId("location")).toHaveText("/work-items");
  });

  test("goes back to the board when the item was opened from it", async ({
    mount,
  }) => {
    const component = await mount(
      <TestRouter
        paths={paths}
        initialEntries={[board, "/work-items/1"]}
        showLocation
      >
        <GoBackOrButton label="Trash" target="list" projectId="p1" />
      </TestRouter>,
    );
    await component.getByRole("button", { name: "Trash" }).click();
    await expect(component.getByTestId("location")).toHaveText(board);
  });

  test("board, item, edit, save, trash returns to the board", async ({
    mount,
  }) => {
    const component = await mount(
      <TestRouter
        paths={paths}
        initialEntries={[board, "/work-items/1", "/work-items/1/edit"]}
        showLocation
      >
        <GoBackOrButton label="Save" target="item" />
        <GoBackOrButton label="Trash" target="list" projectId="p1" />
      </TestRouter>,
    );
    await component.getByRole("button", { name: "Save" }).click();
    await expect(component.getByTestId("location")).toHaveText("/work-items/1");
    await component.getByRole("button", { name: "Trash" }).click();
    await expect(component.getByTestId("location")).toHaveText(board);
  });

  test("shared link to edit, save, falls back to the item page", async ({
    mount,
  }) => {
    const component = await mount(
      <TestRouter
        paths={paths}
        initialEntries={["/work-items/1/edit"]}
        showLocation
      >
        <GoBackOrButton label="Save" target="item" />
      </TestRouter>,
    );
    await component.getByRole("button", { name: "Save" }).click();
    await expect(component.getByTestId("location")).toHaveText("/work-items/1");
  });
});
