import { expect, test } from "../../../playwright/fixtures.ts";
import type { Project } from "../../lib/projects";
import { ProjectPicker } from "./ProjectPicker";

const projects: Project[] = [
  {
    id: "p1",
    name: "kangaroo",
    description: null,
    created_at: "2026-01-01T00:00:00Z",
    modified_at: "2026-01-01T00:00:00Z",
  },
  {
    id: "p2",
    name: "lab",
    description: null,
    created_at: "2026-01-01T00:00:00Z",
    modified_at: "2026-01-01T00:00:00Z",
  },
];

test.describe("ProjectPicker", () => {
  test("shows the name of the selected project when writing IDs", async ({
    mount,
  }) => {
    const component = await mount(
      <ProjectPicker
        value="p1"
        projects={projects}
        useId={true}
        onChange={() => {}}
      />,
    );
    await expect(component.getByLabel("Value")).toHaveText("kangaroo");
  });

  test("shows the raw value when no project matches", async ({ mount }) => {
    const component = await mount(
      <ProjectPicker
        value="ghost"
        projects={projects}
        useId={false}
        onChange={() => {}}
      />,
    );
    await expect(component.getByLabel("Value")).toHaveText("ghost");
  });

  test("shows a placeholder when no value is set", async ({ mount }) => {
    const component = await mount(
      <ProjectPicker
        value=""
        projects={projects}
        useId={true}
        onChange={() => {}}
      />,
    );
    await expect(component.getByLabel("Value")).toHaveText("Choose a project");
  });

  test("writes the project ID when useId is set", async ({ mount }) => {
    const changes: string[] = [];
    const component = await mount(
      <ProjectPicker
        value="p1"
        projects={projects}
        useId={true}
        onChange={(value) => changes.push(value)}
      />,
    );
    await component.getByLabel("Value").click();
    await component.getByRole("button", { name: "lab", exact: true }).click();
    expect(changes).toEqual(["p2"]);
  });

  test("writes the project name when useId is not set", async ({ mount }) => {
    const changes: string[] = [];
    const component = await mount(
      <ProjectPicker
        value="kangaroo"
        projects={projects}
        useId={false}
        onChange={(value) => changes.push(value)}
      />,
    );
    await component.getByLabel("Value").click();
    await component.getByRole("button", { name: "lab", exact: true }).click();
    expect(changes).toEqual(["lab"]);
  });

  test("searches by project ID", async ({ mount }) => {
    const component = await mount(
      <ProjectPicker
        value="p1"
        projects={projects}
        useId={true}
        onChange={() => {}}
      />,
    );
    await component.getByLabel("Value").click();
    await component.getByLabel("Search projects").fill("P2");
    await expect(
      component.getByRole("listbox").getByRole("option"),
    ).toHaveCount(1);
    await expect(
      component.getByRole("button", { name: "lab", exact: true }),
    ).toBeVisible();
  });

  test("shows a message when no project matches the search", async ({
    mount,
  }) => {
    const component = await mount(
      <ProjectPicker
        value="p1"
        projects={projects}
        useId={true}
        onChange={() => {}}
      />,
    );
    await component.getByLabel("Value").click();
    await component.getByLabel("Search projects").fill("zzzz");
    await expect(component.getByText("No projects match")).toBeVisible();
    await expect(
      component.getByRole("listbox").getByRole("option"),
    ).toHaveCount(0);
  });

  test("marks the current value as the selected option", async ({ mount }) => {
    const component = await mount(
      <ProjectPicker
        value="p1"
        projects={projects}
        useId={true}
        onChange={() => {}}
      />,
    );
    await component.getByLabel("Value").click();
    await expect(
      component.getByRole("option", { name: "kangaroo" }),
    ).toHaveAttribute("aria-selected", "true");
    await expect(
      component.getByRole("option", { name: "lab" }),
    ).toHaveAttribute("aria-selected", "false");
  });

  test("closes and returns focus to the button after choosing", async ({
    mount,
  }) => {
    const component = await mount(
      <ProjectPicker
        value="p1"
        projects={projects}
        useId={true}
        onChange={() => {}}
      />,
    );
    await component.getByLabel("Value").click();
    await component.getByRole("button", { name: "lab", exact: true }).click();
    await expect(component.getByLabel("Search projects")).toHaveCount(0);
    await expect(component.getByLabel("Value")).toBeFocused();
  });
});
