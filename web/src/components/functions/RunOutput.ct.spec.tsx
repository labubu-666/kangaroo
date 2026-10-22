import { expect, test } from "../../../playwright/fixtures.ts";
import { RunOutput } from "./RunOutput";

const BASE = {
  id: "inv-1",
  function_id: "fn-1",
  logs: "",
  result: null,
  error: null,
  created_at: "2026-01-01T00:00:00Z",
  modified_at: "2026-01-01T00:00:00Z",
};

test.describe("RunOutput", () => {
  test("shows the status, logs and result", async ({ mount }) => {
    const component = await mount(
      <RunOutput
        result={{
          ...BASE,
          status: "SUCCESS",
          logs: "42\nwarn",
          result: { count: 3 },
        }}
      />,
    );
    await expect(component.getByText("SUCCESS")).toHaveClass(/text-green-700/);
    await expect(component.getByText("42")).toBeVisible();
    await expect(component.getByText('"count": 3')).toBeVisible();
  });

  test("shows the error for a failed run", async ({ mount }) => {
    const component = await mount(
      <RunOutput
        result={{ ...BASE, status: "ERROR", error: "Exited with code 1" }}
      />,
    );
    await expect(component.getByText("ERROR")).toHaveClass(/text-danger-hover/);
    await expect(component.getByText("Exited with code 1")).toBeVisible();
    await expect(component.getByText("(empty)")).toHaveCount(1);
  });

  test("shows null when the script returned nothing", async ({ mount }) => {
    const component = await mount(
      <RunOutput result={{ ...BASE, status: "SUCCESS" }} />,
    );
    await expect(component.getByText("null")).toBeVisible();
  });
});
