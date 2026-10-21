import { Fragment, useState } from "react";
import type { Project } from "../../lib/projects";
import { ProjectPicker } from "./ProjectPicker";
import {
  BOARD_FIELDS,
  addPart,
  formatCondition,
  isBoolField,
  isEmptyOperator,
  isListOperator,
  isProjectField,
  joinFilter,
  movePart,
  operatorsFor,
  parseCondition,
  parseInput,
  parseList,
  removePart,
  replacePart,
  splitFilter,
  toggleJoin,
  type Condition,
  type Operator,
} from "../../lib/filter-bubbles";

const CONTROL =
  "rounded border border-gray-300 bg-white px-1 py-0.5 text-sm text-gray-800";

const MOVE_BUTTON =
  "flex h-5 w-5 shrink-0 items-center justify-center rounded text-xs leading-none text-gray-500 hover:bg-gray-200 hover:text-gray-900 disabled:text-gray-300 disabled:hover:bg-transparent";

export function FilterBubbles({
  filter,
  onChange,
  projects,
  fields = BOARD_FIELDS,
}: {
  filter?: string;
  onChange: (filter: string | undefined) => void;
  projects: Project[];
  fields?: readonly string[];
}) {
  const [draft, setDraft] = useState("");
  const parts = splitFilter(filter);
  const { texts, joins } = parts;

  // Every change goes through the parts model, then back to one filter string
  const update = (next: typeof parts) => onChange(joinFilter(next));

  return (
    <div className="flex flex-wrap items-center gap-2">
      {texts.map((text, index) => {
        const key = `${index}:${text}`;
        const condition = parseCondition(text, fields);
        const bubble = condition ? (
          <ConditionBubble
            condition={condition}
            fields={fields}
            projects={projects}
            onChange={(next) =>
              update(replacePart(parts, index, formatCondition(next)))
            }
            onRemove={() => update(removePart(parts, index))}
          />
        ) : (
          <RawBubble
            text={text}
            onChange={(next) =>
              update(
                next
                  ? replacePart(parts, index, next)
                  : removePart(parts, index),
              )
            }
            onRemove={() => update(removePart(parts, index))}
          />
        );
        return (
          <Fragment key={key}>
            {index > 0 && (
              <JoinToggle
                join={joins[index - 1]}
                onToggle={() => update(toggleJoin(parts, index - 1))}
              />
            )}
            <div className="flex items-center gap-1">
              <button
                type="button"
                aria-label="Move filter left"
                disabled={index === 0}
                onClick={() => update(movePart(parts, index, -1))}
                className={MOVE_BUTTON}
              >
                ◀
              </button>
              {bubble}
              <button
                type="button"
                aria-label="Move filter right"
                disabled={index === texts.length - 1}
                onClick={() => update(movePart(parts, index, 1))}
                className={MOVE_BUTTON}
              >
                ▶
              </button>
            </div>
          </Fragment>
        );
      })}
      <button
        type="button"
        onClick={() =>
          update(
            addPart(
              parts,
              formatCondition({ field: "title", op: "~", values: [""] }),
            ),
          )
        }
        className="rounded px-2 py-1 text-sm font-medium text-blue-600 hover:bg-blue-50"
      >
        + Filter
      </button>
      <input
        aria-label="Add filter"
        type="text"
        value={draft}
        placeholder="key:value or expression"
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            update(addPart(parts, parseInput(draft, fields)));
            setDraft("");
          }
        }}
        className="rounded border border-gray-300 px-2 py-1 text-sm"
      />
    </div>
  );
}

// Clickable `and` / `or` between two bubbles
function JoinToggle({
  join,
  onToggle,
}: {
  join: string;
  onToggle: () => void;
}) {
  return (
    <button
      type="button"
      aria-label={`Join ${join}, click to change`}
      onClick={onToggle}
      className="rounded px-1.5 py-0.5 text-xs font-semibold uppercase text-blue-700 hover:bg-blue-100"
    >
      {join}
    </button>
  );
}

function ConditionBubble({
  condition,
  fields,
  projects,
  onChange,
  onRemove,
}: {
  condition: Condition;
  fields: readonly string[];
  projects: Project[];
  onChange: (condition: Condition) => void;
  onRemove: () => void;
}) {
  const { field, op, values } = condition;
  const listOp = isListOperator(op);
  const current = listOp ? values.join(", ") : (values[0] ?? "");
  // Keyed by the bubble text in the parent, so the draft resets when it changes
  const [draft, setDraft] = useState(current);

  const commit = () => {
    if (draft === current) return;
    onChange({ ...condition, values: listOp ? parseList(draft) : [draft] });
  };

  const projectPicker = isProjectField(field) && (op === "==" || op === "!=");

  return (
    <div className="flex flex-wrap items-center gap-1 rounded border border-blue-200 bg-blue-50 px-2 py-1">
      <select
        aria-label="Field"
        value={field}
        onChange={(e) => {
          const next = e.target.value;
          // Keep the operator only if the new field supports it
          const nextOp = operatorsFor(next).includes(op)
            ? op
            : operatorsFor(next)[0];
          onChange({
            ...condition,
            field: next,
            op: nextOp,
            values: isBoolField(next)
              ? ["true"]
              : isEmptyOperator(nextOp)
                ? []
                : values,
          });
        }}
        className={CONTROL}
      >
        {fields.map((name) => (
          <option key={name} value={name}>
            {name}
          </option>
        ))}
      </select>
      <select
        aria-label="Operator"
        value={op}
        onChange={(e) => {
          const next = e.target.value as Operator;
          onChange({
            ...condition,
            op: next,
            values: isEmptyOperator(next) ? [] : values,
          });
        }}
        className={CONTROL}
      >
        {operatorsFor(field).map((name) => (
          <option key={name} value={name}>
            {name}
          </option>
        ))}
      </select>
      {!isEmptyOperator(op) &&
        (isBoolField(field) ? (
          <select
            aria-label="Value"
            value={current}
            onChange={(e) =>
              onChange({ ...condition, values: [e.target.value] })
            }
            className={CONTROL}
          >
            <option value="true">true</option>
            <option value="false">false</option>
          </select>
        ) : projectPicker ? (
          <ProjectPicker
            value={current}
            projects={projects}
            useId={field === "project.id"}
            onChange={(value) => onChange({ ...condition, values: [value] })}
          />
        ) : (
          <input
            aria-label="Value"
            type="text"
            value={draft}
            placeholder={listOp ? "'a', 'b'" : "text"}
            onChange={(e) => setDraft(e.target.value)}
            onBlur={commit}
            onKeyDown={(e) => {
              if (e.key === "Enter") e.currentTarget.blur();
            }}
            className={`${CONTROL} min-w-[10rem]`}
          />
        ))}
      <button
        type="button"
        aria-label="Remove filter"
        onClick={onRemove}
        className="flex h-5 w-5 shrink-0 items-center justify-center rounded text-xs leading-none text-gray-500 hover:bg-gray-200 hover:text-gray-900"
      >
        ✕
      </button>
    </div>
  );
}

// A filter the bubbles cannot describe (or, not, brackets), edited as text
function RawBubble({
  text,
  onChange,
  onRemove,
}: {
  text: string;
  onChange: (text: string) => void;
  onRemove: () => void;
}) {
  const [draft, setDraft] = useState(text);

  const commit = () => {
    if (draft.trim() !== text) onChange(draft.trim());
  };

  return (
    <div className="flex items-center gap-1 rounded border border-amber-300 bg-amber-50 px-2 py-1">
      <input
        aria-label="Filter expression"
        type="text"
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === "Enter") e.currentTarget.blur();
        }}
        className="min-w-[12rem] bg-transparent font-mono text-sm text-gray-800 outline-none"
      />
      <button
        type="button"
        aria-label="Remove filter"
        onClick={onRemove}
        className="flex h-5 w-5 shrink-0 items-center justify-center rounded text-xs leading-none text-gray-500 hover:bg-gray-200 hover:text-gray-900"
      >
        ✕
      </button>
    </div>
  );
}
