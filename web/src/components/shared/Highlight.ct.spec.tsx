import { expect, test } from "../../../playwright/fixtures.ts";
import { Highlight } from "./Highlight";
import { SearchSnippet } from "./SearchSnippet";

test.describe("Highlight", () => {
  test("wraps matches in mark, ignoring case", async ({ mount }) => {
    const component = await mount(
      <Highlight text="Login fails, LOGIN again" term="login" />,
    );
    const marks = component.locator("mark");
    await expect(marks).toHaveCount(2);
    await expect(marks.nth(0)).toHaveText("Login");
    await expect(marks.nth(1)).toHaveText("LOGIN");
  });

  test("shows the text unchanged when nothing matches", async ({ mount }) => {
    const component = await mount(<Highlight text="Nothing here" term="xyz" />);
    await expect(component.locator("mark")).toHaveCount(0);
    await expect(component).toHaveText("Nothing here");
  });

  test("treats the term as literal text, not a pattern", async ({
    mount,
    page,
  }) => {
    await mount(<Highlight text="cost (USD) here" term="(usd)" />);
    const mark = page.locator("mark");
    await expect(mark).toHaveCount(1);
    await expect(mark).toHaveText("(USD)");
  });
});

test.describe("SearchSnippet", () => {
  test("shows the count of other matches", async ({ mount }) => {
    const component = await mount(
      <SearchSnippet
        hit={{ text: "Login fails", match_count: 3 }}
        term="login"
      />,
    );
    await expect(component).toContainText("+2 more matches");
  });

  test("shows no count for a single match", async ({ mount }) => {
    const component = await mount(
      <SearchSnippet hit={{ text: "Login", match_count: 1 }} term="login" />,
    );
    await expect(component).not.toContainText("more match");
  });

  test("renders nothing without a hit", async ({ mount }) => {
    const component = await mount(<SearchSnippet hit={null} term="login" />);
    await expect(component.locator("p")).toHaveCount(0);
  });
});
