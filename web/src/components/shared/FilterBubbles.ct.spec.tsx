import { expect, test } from "../../../playwright/fixtures.ts";
import type { Project } from "../../lib/projects";
import { FilterBubbles } from "./FilterBubbles";

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

test.describe("FilterBubbles", () => {
  test("shows a project filter as an interactive bubble", async ({ mount }) => {
    const component = await mount(
      <FilterBubbles
        filter="project.id == 'p1'"
        onChange={() => {}}
        projects={projects}
      />,
    );

    await expect(component.getByLabel("Field")).toHaveValue("project.id");
    await expect(component.getByLabel("Operator")).toHaveValue("==");
    await expect(component.getByLabel("Value")).toContainText("kangaroo");
  });

  test("splits an and filter into one bubble per condition", async ({
    mount,
  }) => {
    const component = await mount(
      <FilterBubbles
        filter="summary ~ 'bug' and project.name == 'kangaroo'"
        onChange={() => {}}
        projects={projects}
      />,
    );

    await expect(component.getByLabel("Field")).toHaveCount(2);
  });

  test("shows an or filter as two bubbles with an or join", async ({
    mount,
  }) => {
    const component = await mount(
      <FilterBubbles
        filter="summary ~ 'a' or summary ~ 'b'"
        onChange={() => {}}
        projects={projects}
      />,
    );

    await expect(component.getByLabel("Field")).toHaveCount(2);
    await expect(
      component.getByRole("button", { name: "Join or, click to change" }),
    ).toBeVisible();
  });

  test("keeps a mixed and/or filter as one text bubble", async ({ mount }) => {
    const component = await mount(
      <FilterBubbles
        filter="summary ~ 'a' or summary ~ 'b' and summary ~ 'c'"
        onChange={() => {}}
        projects={projects}
      />,
    );

    await expect(component.getByLabel("Field")).toHaveCount(0);
    await expect(component.getByLabel("Filter expression")).toHaveValue(
      "summary ~ 'a' or summary ~ 'b' and summary ~ 'c'",
    );
  });

  test("toggles the join between bubbles", async ({ mount }) => {
    const changes: string[] = [];
    const component = await mount(
      <FilterBubbles
        filter="summary ~ 'a' and summary ~ 'b'"
        onChange={(filter) => changes.push(filter ?? "")}
        projects={projects}
      />,
    );

    await component.getByRole("button", { name: /Join and/ }).click();

    expect(changes).toEqual(["summary ~ 'a' or summary ~ 'b'"]);
  });

  test("moves a bubble to the right", async ({ mount }) => {
    const changes: string[] = [];
    const component = await mount(
      <FilterBubbles
        filter="summary ~ 'a' and summary ~ 'b'"
        onChange={(filter) => changes.push(filter ?? "")}
        projects={projects}
      />,
    );

    await component
      .getByRole("button", { name: "Move filter right" })
      .first()
      .click();

    expect(changes).toEqual(["summary ~ 'b' and summary ~ 'a'"]);
  });

  test("brackets the earlier bubbles when a join changes", async ({
    mount,
  }) => {
    const changes: string[] = [];
    const component = await mount(
      <FilterBubbles
        filter="summary ~ 'a' and summary ~ 'b' and summary ~ 'c'"
        onChange={(filter) => changes.push(filter ?? "")}
        projects={projects}
      />,
    );

    await component
      .getByRole("button", { name: /Join and/ })
      .last()
      .click();

    expect(changes).toEqual([
      "(summary ~ 'a' and summary ~ 'b') or summary ~ 'c'",
    ]);
  });

  test("changes the operator", async ({ mount }) => {
    const changes: string[] = [];
    const component = await mount(
      <FilterBubbles
        filter="summary ~ 'bug'"
        onChange={(filter) => changes.push(filter ?? "")}
        projects={projects}
      />,
    );

    await component.getByLabel("Operator").selectOption("!=");

    expect(changes).toEqual(["summary != 'bug'"]);
  });

  test("changes a project from the dropdown", async ({ mount }) => {
    const changes: string[] = [];
    const component = await mount(
      <FilterBubbles
        filter="project.id == 'p1'"
        onChange={(filter) => changes.push(filter ?? "")}
        projects={projects}
      />,
    );

    await component.getByLabel("Value").click();
    await component.getByRole("button", { name: "lab", exact: true }).click();

    expect(changes).toEqual(["project.id == 'p2'"]);
  });

  test("shows only the first 3 projects until the user types", async ({
    mount,
  }) => {
    const many: Project[] = Array.from({ length: 5 }, (_, i) => ({
      id: `id-${i}`,
      name: `project ${i}`,
      description: null,
      created_at: "2026-01-01T00:00:00Z",
      modified_at: "2026-01-01T00:00:00Z",
    }));
    const component = await mount(
      <FilterBubbles
        filter="project.name == 'project 0'"
        onChange={() => {}}
        projects={many}
      />,
    );

    await component.getByLabel("Value").click();

    await expect(
      component.getByRole("listbox").getByRole("option"),
    ).toHaveCount(3);
    await expect(component.getByText("2 more, type to search")).toBeVisible();
  });

  test("closes the project panel on Escape", async ({ mount }) => {
    const component = await mount(
      <FilterBubbles
        filter="project.id == 'p1'"
        onChange={() => {}}
        projects={projects}
      />,
    );

    await component.getByLabel("Value").click();
    await expect(component.getByLabel("Search projects")).toBeFocused();
    await component.getByLabel("Search projects").press("Escape");

    await expect(component.getByLabel("Search projects")).toHaveCount(0);
    await expect(component.getByLabel("Value")).toBeFocused();
  });

  test("searches all projects by name", async ({ mount }) => {
    const many: Project[] = Array.from({ length: 5 }, (_, i) => ({
      id: `id-${i}`,
      name: `project ${i}`,
      description: null,
      created_at: "2026-01-01T00:00:00Z",
      modified_at: "2026-01-01T00:00:00Z",
    }));
    const changes: string[] = [];
    const component = await mount(
      <FilterBubbles
        filter="project.name == 'project 0'"
        onChange={(filter) => changes.push(filter ?? "")}
        projects={many}
      />,
    );

    await component.getByLabel("Value").click();
    await component.getByLabel("Search projects").fill("project 4");
    await expect(
      component.getByRole("listbox").getByRole("option"),
    ).toHaveCount(1);
    await component
      .getByRole("button", { name: "project 4", exact: true })
      .click();

    expect(changes).toEqual(["project.name == 'project 4'"]);
  });

  test("edits a text value on Enter", async ({ mount }) => {
    const changes: string[] = [];
    const component = await mount(
      <FilterBubbles
        filter="summary ~ 'bug'"
        onChange={(filter) => changes.push(filter ?? "")}
        projects={projects}
      />,
    );

    await component.getByLabel("Value").fill("login");
    await component.getByLabel("Value").press("Enter");

    expect(changes).toEqual(["summary ~ 'login'"]);
  });

  test("shows a labels contains filter with the contains operator", async ({
    mount,
  }) => {
    const component = await mount(
      <FilterBubbles
        filter="labels contains 'urgent'"
        onChange={() => {}}
        projects={projects}
        fields={["summary", "labels"]}
      />,
    );

    await expect(component.getByLabel("Field")).toHaveValue("labels");
    await expect(component.getByLabel("Operator")).toHaveValue("contains");
    await expect(component.getByLabel("Value")).toHaveValue("urgent");
  });

  test("removes one bubble of an and filter", async ({ mount }) => {
    const changes: string[] = [];
    const component = await mount(
      <FilterBubbles
        filter="summary ~ 'a' and summary ~ 'b'"
        onChange={(filter) => changes.push(filter ?? "")}
        projects={projects}
      />,
    );

    await component
      .getByRole("button", { name: "Remove filter" })
      .first()
      .click();

    expect(changes).toEqual(["summary ~ 'b'"]);
  });

  test("adds a key:value bubble from the add box", async ({ mount }) => {
    const changes: string[] = [];
    const component = await mount(
      <FilterBubbles
        onChange={(filter) => changes.push(filter ?? "")}
        projects={projects}
      />,
    );

    await component.getByLabel("Add filter").fill("project.name:kangaroo");
    await component.getByLabel("Add filter").press("Enter");

    expect(changes).toEqual(["project.name == 'kangaroo'"]);
  });
});
