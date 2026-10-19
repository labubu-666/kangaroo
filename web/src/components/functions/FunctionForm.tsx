import { Link } from "@tanstack/react-router";
import { useState, type FormEvent } from "react";
import { ErrorBanner } from "../shared/ErrorBanner";
import { LabelsEditor } from "../shared/LabelsEditor";
import { CodeEditor } from "./CodeEditor";

export interface FunctionFormValues {
  name: string;
  description: string;
  code: string;
  labels: string[];
}

export function FunctionForm({
  initial,
  submitLabel,
  pendingLabel,
  cancelTo,
  cancelParams,
  disabled,
  error,
  onSubmit,
}: {
  initial: FunctionFormValues;
  submitLabel: string;
  pendingLabel: string;
  cancelTo: "/functions" | "/functions/$id";
  cancelParams?: { id: string };
  disabled: boolean;
  error: string | null;
  onSubmit: (values: FunctionFormValues) => void;
}) {
  const [values, setValues] = useState<FunctionFormValues>(initial);
  const [nameError, setNameError] = useState<string | null>(null);
  const [codeError, setCodeError] = useState<string | null>(null);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setNameError(values.name.trim() ? null : "Name is required");
    setCodeError(values.code.trim() ? null : "Code is required");
    if (!values.name.trim() || !values.code.trim()) return;
    onSubmit(values);
  };

  return (
    <>
      {error && <ErrorBanner>{error}</ErrorBanner>}

      <form
        onSubmit={handleSubmit}
        autoComplete="off"
        className="space-y-4 rounded border border-gray-200 p-4"
      >
        <div className="space-y-2">
          <label htmlFor="name" className="block font-medium">
            Name *
          </label>
          <input
            id="name"
            type="text"
            disabled={disabled}
            placeholder="Enter function name"
            value={values.name}
            onChange={(e) => setValues({ ...values, name: e.target.value })}
            className="w-full rounded border border-gray-300 px-3 py-2"
          />
          {nameError && <p className="text-sm text-red-600">{nameError}</p>}
        </div>

        <div className="space-y-2">
          <label className="block font-medium">Code *</label>
          <p className="text-sm text-gray-500">
            A Python script. Put dependencies in a PEP 723 header, for example{" "}
            <code># /// script</code>.
          </p>
          <CodeEditor
            value={values.code}
            ariaLabel="Code"
            readOnly={disabled}
            placeholder={
              '# /// script\n# dependencies = ["requests"]\n# ///\nprint("hello")'
            }
            onChange={(code) => setValues({ ...values, code })}
          />
          {codeError && <p className="text-sm text-red-600">{codeError}</p>}
        </div>

        <div className="space-y-2">
          <label htmlFor="description" className="block font-medium">
            Description
          </label>
          <textarea
            id="description"
            disabled={disabled}
            placeholder="Enter function description (optional)"
            rows={3}
            value={values.description}
            onChange={(e) =>
              setValues({ ...values, description: e.target.value })
            }
            className="w-full rounded border border-gray-300 px-3 py-2"
          />
        </div>

        <LabelsEditor
          labels={values.labels}
          disabled={disabled}
          onChange={(labels) => setValues({ ...values, labels })}
        />

        <div className="flex flex-wrap gap-3">
          <button
            type="submit"
            disabled={disabled}
            className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:bg-gray-400"
          >
            {disabled ? pendingLabel : submitLabel}
          </button>
          <Link
            to={cancelTo}
            params={cancelParams}
            className="rounded border border-gray-300 px-4 py-2 font-medium hover:bg-gray-50"
          >
            Cancel
          </Link>
        </div>
      </form>
    </>
  );
}
