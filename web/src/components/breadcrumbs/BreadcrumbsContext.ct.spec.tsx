import { expect, test } from "../../../playwright/fixtures.ts";
import { ErrorBoundary, PublishWithoutProvider } from "./BreadcrumbsTest.story";

test.describe("useBreadcrumbs", () => {
  test("throws when used outside BreadcrumbsProvider", async ({
    mount,
    page,
  }) => {
    await mount(
      <ErrorBoundary>
        <PublishWithoutProvider />
      </ErrorBoundary>,
    );
    await expect(page.getByRole("alert")).toHaveText(
      "useBreadcrumbs must be used inside BreadcrumbsProvider",
    );
  });
});
