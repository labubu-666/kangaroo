import { expect, test } from "../../../playwright/fixtures.ts";
import { TestRouter } from "../TestRouter.story";
import { FunctionForm, type FunctionFormValues } from "./FunctionForm";

const empty: FunctionFormValues = {
  name: "",
  description: "",
  code: "",
  labels: [],
};

const paths = ["/", "/functions", "/functions/$id"];

test.describe("FunctionForm", () => {
  test("shows the initial values", async ({ mount }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <FunctionForm
          initial={{
            name: "Hello",
            description: "Says hi",
            code: "print(1)",
            labels: ["demo"],
          }}
          submitLabel="Save"
          pendingLabel="Saving..."
          cancelTo="/functions"
          disabled={false}
          error={null}
          onSubmit={() => {}}
        />
      </TestRouter>,
    );
    await expect(component.getByLabel("Name *")).toHaveValue("Hello");
    await expect(component.getByLabel("Description")).toHaveValue("Says hi");
    await expect(component.getByLabel("Code *")).toHaveValue("print(1)");
    await expect(component.getByText("demo", { exact: true })).toBeVisible();
  });

  test("requires a name and code before submitting", async ({ mount }) => {
    let submitted = false;
    const component = await mount(
      <TestRouter paths={paths}>
        <FunctionForm
          initial={empty}
          submitLabel="Create"
          pendingLabel="Creating..."
          cancelTo="/functions"
          disabled={false}
          error={null}
          onSubmit={() => {
            submitted = true;
          }}
        />
      </TestRouter>,
    );
    await component.getByRole("button", { name: "Create" }).click();
    await expect(component.getByText("Name is required")).toBeVisible();
    await expect(component.getByText("Code is required")).toBeVisible();
    expect(submitted).toBe(false);
  });

  test("submits the entered values", async ({ mount }) => {
    const submitted: FunctionFormValues[] = [];
    const component = await mount(
      <TestRouter paths={paths}>
        <FunctionForm
          initial={empty}
          submitLabel="Create"
          pendingLabel="Creating..."
          cancelTo="/functions"
          disabled={false}
          error={null}
          onSubmit={(values) => submitted.push(values)}
        />
      </TestRouter>,
    );
    await component.getByLabel("Name *").fill("Hello");
    await component.getByLabel("Code *").fill('print("hi")');
    await component.getByRole("button", { name: "Create" }).click();
    expect(submitted).toEqual([
      { name: "Hello", description: "", code: 'print("hi")', labels: [] },
    ]);
  });

  test("shows the pending label and disables the form while saving", async ({
    mount,
  }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <FunctionForm
          initial={empty}
          submitLabel="Create"
          pendingLabel="Creating..."
          cancelTo="/functions"
          disabled={true}
          error={null}
          onSubmit={() => {}}
        />
      </TestRouter>,
    );
    await expect(
      component.getByRole("button", { name: "Creating..." }),
    ).toBeDisabled();
    await expect(component.getByLabel("Name *")).toBeDisabled();
  });

  test("shows the server error", async ({ mount }) => {
    const component = await mount(
      <TestRouter paths={paths}>
        <FunctionForm
          initial={empty}
          submitLabel="Create"
          pendingLabel="Creating..."
          cancelTo="/functions"
          disabled={false}
          error="Failed to create function"
          onSubmit={() => {}}
        />
      </TestRouter>,
    );
    await expect(
      component.getByText("Failed to create function"),
    ).toBeVisible();
  });
});
