import { expect, test } from "../../../playwright/fixtures.ts";
import { RunOutput } from "./RunOutput";

test.describe("RunOutput", () => {
  test("shows the exit code and both streams", async ({ mount }) => {
    const component = await mount(
      <RunOutput result={{ stdout: "42\n", stderr: "warn", exit_code: 0 }} />,
    );
    await expect(component.getByText("Exit code 0")).toBeVisible();
    await expect(component.getByText("42")).toBeVisible();
    await expect(component.getByText("warn")).toBeVisible();
  });

  test("marks a non-zero exit code and shows empty streams", async ({
    mount,
  }) => {
    const component = await mount(
      <RunOutput result={{ stdout: "", stderr: "", exit_code: 1 }} />,
    );
    await expect(component.getByText("Exit code 1")).toHaveClass(
      /text-red-700/,
    );
    await expect(component.getByText("(empty)")).toHaveCount(2);
  });
});
