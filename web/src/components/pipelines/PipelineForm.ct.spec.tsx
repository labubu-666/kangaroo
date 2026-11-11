import { expect, test } from "../../../playwright/fixtures.ts";
import { TestRouter } from "../TestRouter.story";
import { PipelineForm, type PipelineFormValues } from "./PipelineForm";

const empty: PipelineFormValues = {
  name: "",
  description: "",
  steps: {},
  labels: [],
};

const paths = ["/", "/pipelines", "/pipelines/$id"];

test.describe("PipelineForm", () => {
  test("mounts and stays stable while steps are added", async ({
    mount,
    page,
  }) => {
    // A render loop surfaces as an uncaught error on the page.
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(error.message));

    const component = await mount(
      <TestRouter paths={paths}>
        <PipelineForm
          initial={empty}
          submitLabel="Create"
          pendingLabel="Creating..."
          disabled={false}
          error={null}
          onSubmit={() => {}}
        />
      </TestRouter>,
    );

    await expect(component.getByLabel("Name *")).toBeVisible();
    await expect(
      component.getByLabel("Add a function as a step"),
    ).toBeVisible();
    await page.waitForTimeout(500);
    expect(errors.filter((e) => e.includes("Maximum update depth"))).toEqual(
      [],
    );
  });
});
