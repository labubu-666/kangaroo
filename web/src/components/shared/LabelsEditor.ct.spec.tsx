import { expect, test } from "../../../playwright/fixtures.ts";
import { LabelsEditor } from "./LabelsEditor";

test.describe("LabelsEditor", () => {
  test("shows the existing labels", async ({ mount }) => {
    const component = await mount(
      <LabelsEditor labels={["news", "urgent"]} onChange={() => {}} />,
    );

    await expect(component.getByText("news", { exact: true })).toBeVisible();
    await expect(component.getByText("urgent", { exact: true })).toBeVisible();
  });

  test("adds a trimmed label on Enter", async ({ mount }) => {
    const changes: string[][] = [];
    const component = await mount(
      <LabelsEditor
        labels={["news"]}
        onChange={(labels) => changes.push(labels)}
      />,
    );

    await component.getByRole("textbox").fill("  derstandard:1  ");
    await component.getByRole("textbox").press("Enter");

    expect(changes).toEqual([["news", "derstandard:1"]]);
    await expect(component.getByRole("textbox")).toHaveValue("");
  });

  test("adds a pending label when the input loses focus", async ({ mount }) => {
    const changes: string[][] = [];
    const component = await mount(
      <LabelsEditor labels={[]} onChange={(labels) => changes.push(labels)} />,
    );

    await component.getByRole("textbox").fill("news");
    await component.getByRole("textbox").blur();

    expect(changes).toEqual([["news"]]);
    await expect(component.getByRole("textbox")).toHaveValue("");
  });

  test("ignores blank and duplicate labels", async ({ mount }) => {
    const changes: string[][] = [];
    const component = await mount(
      <LabelsEditor
        labels={["news"]}
        onChange={(labels) => changes.push(labels)}
      />,
    );

    await component.getByRole("textbox").fill("   ");
    await component.getByRole("textbox").press("Enter");
    await component.getByRole("textbox").fill("news");
    await component.getByRole("textbox").press("Enter");

    expect(changes).toEqual([]);
  });

  test("shows the add label placeholder", async ({ mount }) => {
    const component = await mount(
      <LabelsEditor labels={[]} onChange={() => {}} />,
    );

    await expect(component.getByRole("textbox")).toHaveAttribute(
      "placeholder",
      "Add a label",
    );
  });

  test("removes a label", async ({ mount }) => {
    const changes: string[][] = [];
    const component = await mount(
      <LabelsEditor
        labels={["news", "urgent"]}
        onChange={(labels) => changes.push(labels)}
      />,
    );

    await component.getByRole("button", { name: "Remove label news" }).click();

    expect(changes).toEqual([["urgent"]]);
  });
});
