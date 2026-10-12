import { expect, test } from "../../../playwright/fixtures.ts";
import { TestRouter } from "../../components/TestRouter.story";
import { CreateProjectForm } from "../../components/projects/CreateProjectForm";

const paths = ["/", "/projects"];

test.beforeEach(async ({ page }) => {
  await page.route("**/api/v1/project-templates/**", (route) =>
    route.fulfill({
      json: { default: "To Do List", names: ["To Do List", "Bug Tracker"] },
    }),
  );
});

test.describe("create project template picker", () => {
  test("selects the server's default template", async ({ mount }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <CreateProjectForm />
      </TestRouter>,
    );
    await expect(component.getByLabel("Template *")).toHaveValue("To Do List");
  });

  test("sends the chosen template with the new project", async ({
    mount,
    page,
  }) => {
    let sent: unknown = null;
    await page.route("**/api/v1/projects/", async (route) => {
      if (route.request().method() === "POST") {
        sent = route.request().postDataJSON();
        return route.fulfill({
          status: 201,
          json: { id: "p1", name: "Alpha", description: null, labels: [] },
        });
      }
      return route.fulfill({
        json: { results: [], limit: 10, offset: 0, total: 0 },
      });
    });
    const component = await mount(
      <TestRouter paths={paths}>
        <CreateProjectForm />
      </TestRouter>,
    );
    await component.getByLabel("Name *").fill("Alpha");
    await component.getByLabel("Template *").selectOption("Bug Tracker");
    await component.getByRole("button", { name: "Create" }).click();
    await expect
      .poll(() => sent)
      .toMatchObject({
        name: "Alpha",
        template: "Bug Tracker",
      });
  });
});
