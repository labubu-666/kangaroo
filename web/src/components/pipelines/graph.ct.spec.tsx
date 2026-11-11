import { expect, test } from "../../../playwright/fixtures.ts";
import {
  graphToSteps,
  layoutDepths,
  stepsToGraph,
  uniqueStepName,
} from "./graph";

const steps = {
  a: { function_id: "f-a", on_success: ["b"], on_failure: ["c"] },
  b: { function_id: "f-b", on_success: ["d"], on_failure: [] },
  c: { function_id: "f-c", on_success: [], on_failure: [] },
  d: { function_id: "f-d", on_success: [], on_failure: [] },
};

test.describe("pipeline graph", () => {
  test("places each step in the column of its longest path", () => {
    expect(layoutDepths(steps)).toEqual(
      new Map([
        ["a", 0],
        ["b", 1],
        ["c", 1],
        ["d", 2],
      ]),
    );
  });

  test("turns steps into nodes and outcome-tagged edges", () => {
    const { nodes, edges } = stepsToGraph(steps);
    expect(nodes.map((node) => node.id).sort()).toEqual(["a", "b", "c", "d"]);
    expect(edges).toHaveLength(3);
    expect(edges.find((edge) => edge.target === "c")).toMatchObject({
      sourceHandle: "failure",
      data: { outcome: "failure" },
    });
  });

  test("converts the canvas back to the same definition", () => {
    const { nodes, edges } = stepsToGraph(steps);
    expect(graphToSteps(nodes, edges)).toEqual(steps);
  });

  test("keeps the function each step refers to", () => {
    const { nodes, edges } = stepsToGraph(steps);
    expect(graphToSteps(nodes, edges)["b"].function_id).toBe("f-b");
  });

  test("names a repeated function's step uniquely", () => {
    expect(uniqueStepName(new Set(), "check")).toBe("check");
    expect(uniqueStepName(new Set(["check"]), "check")).toBe("check-2");
    expect(uniqueStepName(new Set(["check", "check-2"]), "check")).toBe(
      "check-3",
    );
  });

  test("keeps a step with no connections", () => {
    const lone = { x: { function_id: "f-x", on_success: [], on_failure: [] } };
    const { nodes, edges } = stepsToGraph(lone);
    expect(graphToSteps(nodes, edges)).toEqual(lone);
  });
});
