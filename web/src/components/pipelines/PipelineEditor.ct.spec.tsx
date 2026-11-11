import { expect, test } from "../../../playwright/fixtures.ts";
import { TestRouter } from "../TestRouter.story";
import { PipelineEditor } from "./PipelineEditor";

const steps = {
  a: { function_id: "f-a", on_success: ["b"], on_failure: [] },
  b: { function_id: "f-b", on_success: [], on_failure: ["c"] },
  c: { function_id: "f-c", on_success: [], on_failure: [] },
};

test.describe("PipelineEditor", () => {
  test("deleting a step removes it from the reported definition", async ({
    mount,
  }) => {
    const changes: Record<string, unknown>[] = [];
    const component = await mount(
      <TestRouter>
        <PipelineEditor
          initialSteps={steps}
          disabled={false}
          onChange={(next) => changes.push(next)}
        />
      </TestRouter>,
    );

    await component.getByRole("button", { name: "Delete b" }).click();

    await expect(
      component.getByRole("button", { name: "Delete b" }),
    ).toHaveCount(0);
    expect(changes.at(-1)).toEqual({
      a: { function_id: "f-a", on_success: [], on_failure: [] },
      c: { function_id: "f-c", on_success: [], on_failure: [] },
    });
  });
});
