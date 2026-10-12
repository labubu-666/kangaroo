import { useState } from "react";

export function LabelsEditor({
  labels,
  onChange,
  disabled,
}: {
  labels: string[];
  onChange: (labels: string[]) => void;
  disabled?: boolean;
}) {
  const [draft, setDraft] = useState("");

  const addLabel = () => {
    const text = draft.trim();
    setDraft("");
    if (!text || labels.includes(text)) return;
    onChange([...labels, text]);
  };

  const removeLabel = (label: string) => {
    onChange(labels.filter((existing) => existing !== label));
  };

  return (
    <div>
      <label
        htmlFor="new-label"
        className="block text-sm font-medium text-gray-700"
      >
        Labels
      </label>
      <ul className="mt-2 flex flex-wrap gap-2">
        {labels.map((label) => (
          <li
            key={label}
            className="flex items-center gap-1 rounded bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-700"
          >
            <span>{label}</span>
            <button
              type="button"
              aria-label={`Remove label ${label}`}
              onClick={() => removeLabel(label)}
              disabled={disabled}
              className="text-gray-500 hover:text-gray-900 disabled:text-gray-300"
            >
              ✕
            </button>
          </li>
        ))}
      </ul>
      <input
        id="new-label"
        type="text"
        value={draft}
        placeholder="Add a label"
        disabled={disabled}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            addLabel();
          }
        }}
        className="mt-2 w-full rounded border border-gray-300 px-3 py-2"
      />
    </div>
  );
}
