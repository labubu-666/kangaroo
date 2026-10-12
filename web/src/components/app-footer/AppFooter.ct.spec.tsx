import { expect, test } from "../../../playwright/fixtures.ts";
import { AppFooter } from "./AppFooter";
import { TestRouter } from "../TestRouter.story";

test.describe("AppFooter", () => {
  test("renders a footer landmark", async ({ mount, page }) => {
    await mount(
      <TestRouter>
        <AppFooter />
      </TestRouter>,
    );
    await expect(page.getByRole("contentinfo")).toBeVisible();
  });

  test("renders the hardcoded version", async ({ mount }) => {
    const component = await mount(
      <TestRouter>
        <AppFooter />
      </TestRouter>,
    );
    await expect(component.getByText("v0.0.0")).toBeVisible();
  });

  test("links Docs to the docs home", async ({ mount }) => {
    const component = await mount(
      <TestRouter paths={["/", "/docs"]}>
        <AppFooter />
      </TestRouter>,
    );
    await expect(component.getByRole("link", { name: "Docs" })).toHaveAttribute(
      "href",
      "/docs",
    );
  });

  test("renders a link to the api docs", async ({ mount }) => {
    const component = await mount(
      <TestRouter>
        <AppFooter />
      </TestRouter>,
    );
    await expect(component.getByRole("link", { name: "API" })).toHaveAttribute(
      "href",
      "/api/v1/docs",
    );
  });

  test("opens the api docs in a new tab", async ({ mount }) => {
    const component = await mount(
      <TestRouter>
        <AppFooter />
      </TestRouter>,
    );
    await expect(component.getByRole("link", { name: "API" })).toHaveAttribute(
      "target",
      "_blank",
    );
  });
});
