import { expect, test } from "../../../playwright/fixtures.ts";
import { DoneStatusWarning } from "./DoneStatusWarning";
import { lacksDoneStatus } from "../../lib/done-status";

test("explains why finished work can't be counted", async ({ mount }) => {
  const component = await mount(<DoneStatusWarning />);
  await expect(component).toContainText("No status is in the Done category");
});

test("lacks a Done status only when statuses exist and none is done", () => {
  expect(lacksDoneStatus(["todo", "in_progress"])).toBe(true);
  expect(lacksDoneStatus(["todo", "done"])).toBe(false);
  expect(lacksDoneStatus([])).toBe(false);
});
