import { Link } from "@tanstack/react-router";
import { useState, type FormEvent } from "react";
import { ErrorBanner } from "../shared/ErrorBanner";
import { LabelsEditor } from "../shared/LabelsEditor";
import { CodeEditor } from "../functions/CodeEditor";

export interface ArticleFormValues {
  title: string;
  body: string;
  labels: string[];
}

export function ArticleForm({
  initial,
  submitLabel,
  pendingLabel,
  cancelTo,
  cancelParams,
  disabled,
  error,
  onSubmit,
}: {
  initial: ArticleFormValues;
  submitLabel: string;
  pendingLabel: string;
  cancelTo: "/articles" | "/articles/$id";
  cancelParams?: { id: string };
  disabled: boolean;
  error: string | null;
  onSubmit: (values: ArticleFormValues) => void;
}) {
  const [values, setValues] = useState<ArticleFormValues>(initial);
  const [titleError, setTitleError] = useState<string | null>(null);
  const [bodyError, setBodyError] = useState<string | null>(null);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setTitleError(values.title.trim() ? null : "Title is required");
    setBodyError(values.body.trim() ? null : "Body is required");
    if (!values.title.trim() || !values.body.trim()) return;
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
          <label htmlFor="title" className="block font-medium">
            Title *
          </label>
          <input
            id="title"
            type="text"
            disabled={disabled}
            placeholder="Enter article title"
            value={values.title}
            onChange={(e) => setValues({ ...values, title: e.target.value })}
            className="w-full rounded border border-gray-300 px-3 py-2"
          />
          {titleError && <p className="text-sm text-red-600">{titleError}</p>}
        </div>

        <div className="space-y-2">
          <span className="block font-medium">Body *</span>
          <CodeEditor
            value={values.body}
            ariaLabel="Body"
            language="markdown"
            readOnly={disabled}
            placeholder="Write the article in Markdown"
            onChange={(body) => setValues({ ...values, body })}
          />
          {bodyError && <p className="text-sm text-red-600">{bodyError}</p>}
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
