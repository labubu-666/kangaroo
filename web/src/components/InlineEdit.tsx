import { useState, type FormEvent, type ReactNode } from "react";
import { useMutation } from "@tanstack/react-query";
import { ErrorBanner } from "./shared/ErrorBanner";
import { CodeEditor } from "./functions/CodeEditor";

export function InlineEdit({
  value,
  onSave,
  children,
  multiline = false,
  language,
  fill = false,
  placeholder,
  ariaLabel,
  requiredMessage,
  textClassName,
}: {
  value: string;
  onSave: (draft: string) => Promise<unknown>;
  children: ReactNode;
  multiline?: boolean;
  // Renders CodeMirror instead of a textarea, so the text gets syntax highlighting.
  language?: "python" | "markdown";
  // Stretches the view to fill its parent's height.
  fill?: boolean;
  placeholder?: string;
  ariaLabel: string;
  requiredMessage?: string;
  textClassName?: string;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: onSave,
    onSuccess: () => setIsEditing(false),
  });

  const startEditing = () => {
    setDraft(value);
    setValidationError(null);
    mutation.reset();
    setIsEditing(true);
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (requiredMessage && !draft.trim()) {
      setValidationError(requiredMessage);
      return;
    }
    mutation.mutate(draft);
  };

  const inputClassName = `w-full rounded border border-gray-300 px-3 py-2 ${textClassName ?? ""}`;

  if (!isEditing) {
    return (
      <div
        role="button"
        tabIndex={0}
        aria-label={`Edit ${ariaLabel}`}
        onClick={(e) => {
          if ((e.target as HTMLElement).closest("a")) return;
          startEditing();
        }}
        onKeyDown={(e) => {
          if (e.key === "Enter") startEditing();
        }}
        className={`cursor-pointer ${fill ? "flex flex-1 flex-col" : ""}`}
      >
        {children}
      </div>
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      className={`space-y-3 ${fill ? "flex flex-1 flex-col" : ""}`}
    >
      {mutation.error && <ErrorBanner>{mutation.error.message}</ErrorBanner>}
      {language ? (
        <CodeEditor
          value={draft}
          onChange={setDraft}
          readOnly={mutation.isPending}
          ariaLabel={ariaLabel}
          placeholder={placeholder}
          language={language}
          grow
          stretch={fill}
        />
      ) : multiline ? (
        <textarea
          aria-label={ariaLabel}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          disabled={mutation.isPending}
          placeholder={placeholder}
          rows={6}
          className={inputClassName}
        />
      ) : (
        <input
          type="text"
          aria-label={ariaLabel}
          value={draft}
          onChange={(e) => {
            setDraft(e.target.value);
            setValidationError(null);
          }}
          disabled={mutation.isPending}
          placeholder={placeholder}
          className={inputClassName}
        />
      )}
      {validationError && (
        <p className="text-sm text-red-600">{validationError}</p>
      )}
      <div className="flex flex-wrap gap-3">
        <button
          type="submit"
          disabled={mutation.isPending}
          className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:bg-gray-400"
        >
          {mutation.isPending ? "Saving..." : "Save"}
        </button>
        <button
          type="button"
          onClick={() => setIsEditing(false)}
          disabled={mutation.isPending}
          className="rounded border border-gray-300 px-4 py-2 font-medium hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
