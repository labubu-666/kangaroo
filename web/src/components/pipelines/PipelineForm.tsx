import { Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useCallback, useRef, useState, type FormEvent } from "react";
import { fetchFunctions } from "../../lib/functions";
import { ErrorBanner } from "../shared/ErrorBanner";
import { LabelsEditor } from "../shared/LabelsEditor";
import { PipelineEditor, type PipelineEditorHandle } from "./PipelineEditor";
import type { Steps } from "./graph";

export interface PipelineFormValues {
  name: string;
  description: string;
  steps: Steps;
  labels: string[];
}

export function PipelineForm({
  initial,
  submitLabel,
  pendingLabel,
  disabled,
  error,
  onSubmit,
}: {
  initial: PipelineFormValues;
  submitLabel: string;
  pendingLabel: string;
  disabled: boolean;
  error: string | null;
  onSubmit: (values: PipelineFormValues) => void;
}) {
  const [values, setValues] = useState<PipelineFormValues>(initial);
  const [nameError, setNameError] = useState<string | null>(null);
  const [stepsError, setStepsError] = useState<string | null>(null);

  const { data: functions } = useQuery({
    queryKey: ["functions", "names"],
    queryFn: () => fetchFunctions(100, 0),
  });
  const available = functions?.results ?? [];

  const editorRef = useRef<PipelineEditorHandle>(null);

  const handleCanvasChange = useCallback((steps: Steps) => {
    setValues((current) => ({ ...current, steps }));
  }, []);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const steps = values.steps;
    setNameError(values.name.trim() ? null : "Name is required");
    setStepsError(Object.keys(steps).length ? null : "Add at least one step");
    if (!values.name.trim() || Object.keys(steps).length === 0) return;
    onSubmit(values);
  };

  return (
    <>
      {error && <ErrorBanner>{error}</ErrorBanner>}

      <form
        onSubmit={handleSubmit}
        autoComplete="off"
        className="space-y-4 rounded border border-border p-4"
      >
        <div className="space-y-2">
          <label htmlFor="name" className="block font-medium">
            Name *
          </label>
          <input
            id="name"
            type="text"
            disabled={disabled}
            placeholder="Enter pipeline name"
            value={values.name}
            onChange={(e) => setValues({ ...values, name: e.target.value })}
            className="w-full rounded border border-border-strong px-3 py-2"
          />
          {nameError && <p className="text-sm text-danger">{nameError}</p>}
        </div>

        <div className="space-y-2">
          <label htmlFor="description" className="block font-medium">
            Description
          </label>
          <textarea
            id="description"
            disabled={disabled}
            placeholder="Enter pipeline description (optional)"
            rows={3}
            value={values.description}
            onChange={(e) =>
              setValues({ ...values, description: e.target.value })
            }
            className="w-full rounded border border-border-strong px-3 py-2"
          />
        </div>

        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-3">
            <label htmlFor="add-step" className="font-medium">
              Add a function as a step
            </label>
            <select
              id="add-step"
              disabled={disabled || available.length === 0}
              value=""
              onChange={(e) => {
                const fn = available.find((f) => f.id === e.target.value);
                if (fn) editorRef.current?.addStep(fn.id, fn.name);
              }}
              className="rounded border border-border-strong px-3 py-2"
            >
              <option value="">
                {available.length ? "Choose a function" : "No functions saved"}
              </option>
              {available.map((fn) => (
                <option key={fn.id} value={fn.id}>
                  {fn.name}
                </option>
              ))}
            </select>
          </div>
          <p className="text-sm text-fg-muted">
            Drag from a step&apos;s green handle to set what runs on success,
            and from its red handle to set what runs on failure. Steps with no
            handle connected end the run.
          </p>
          <PipelineEditor
            ref={editorRef}
            initialSteps={initial.steps}
            disabled={disabled}
            onChange={handleCanvasChange}
          />
          {stepsError && <p className="text-sm text-danger">{stepsError}</p>}
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
            className="rounded bg-primary px-4 py-2 font-medium text-on-primary hover:bg-primary-hover disabled:bg-fg-disabled"
          >
            {disabled ? pendingLabel : submitLabel}
          </button>
          <Link
            to="/pipelines"
            className="rounded border border-border-strong px-4 py-2 font-medium hover:bg-surface-muted"
          >
            Cancel
          </Link>
        </div>
      </form>
    </>
  );
}
