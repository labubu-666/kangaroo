import { expect, test } from "../../playwright/fixtures.ts";
import { statusIdFromFilter, withStatus } from "./filter-bubbles";

const P = "proj-1";

test.describe("withStatus", () => {
  test("adds a status to a project-only filter", () => {
    expect(withStatus(`project.id == '${P}'`, "s1")).toBe(
      `project.id == '${P}' and status == 's1'`,
    );
  });

  test("replaces an existing status condition", () => {
    expect(withStatus(`project.id == '${P}' and status == 's1'`, "s2")).toBe(
      `project.id == '${P}' and status == 's2'`,
    );
  });

  test("removes the status when All statuses is chosen", () => {
    expect(
      withStatus(`project.id == '${P}' and status == 's1'`, undefined),
    ).toBe(`project.id == '${P}'`);
  });

  test("keeps other conditions and their order", () => {
    expect(
      withStatus(
        `status == 's1' and title ~ 'bug' and project.id == '${P}'`,
        "s2",
      ),
    ).toBe(`title ~ 'bug' and project.id == '${P}' and status == 's2'`);
  });

  test("brackets a mixed or before adding the status", () => {
    expect(withStatus(`project.id == '${P}' or title ~ 'x'`, "s1")).toBe(
      `(project.id == '${P}' or title ~ 'x') and status == 's1'`,
    );
  });

  test("never adds a status without a project in the filter", () => {
    expect(withStatus(undefined, "s1")).toBeUndefined();
    expect(withStatus("title ~ 'x'", "s1")).toBe("title ~ 'x'");
  });

  test("reads back the status id that was written", () => {
    expect(statusIdFromFilter(`project.id == '${P}' and status == 'abc'`)).toBe(
      "abc",
    );
    expect(statusIdFromFilter(`project.id == '${P}'`)).toBeUndefined();
  });
});
