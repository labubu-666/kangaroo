import { useState } from "react";
import {
  createStatus,
  createTransition,
  createWorkItemType,
  deleteTransition,
  updateStatus,
  updateWorkItemType,
  type ProjectStatus,
  type StatusCategory,
  type StatusTransition,
  type TypeLevel,
  type WorkItemType,
} from "../../lib/workflow";
import { ReorderButtons } from "./ReorderButtons";

export const CATEGORY_LABELS: Record<StatusCategory, string> = {
  todo: "To do",
  in_progress: "In progress",
  done: "Done",
};

const LEVEL_LABELS: Record<TypeLevel, string> = {
  standard: "Standard",
  subtask: "Subtask",
};

const FIELD = "rounded border border-gray-300 px-3 py-2 disabled:bg-gray-100";
const PRIMARY =
  "rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:bg-gray-400";
const DANGER =
  "rounded border border-red-300 px-3 py-1 text-sm text-red-700 hover:bg-red-50 disabled:text-gray-400";

// Swaps positions with the neighbour, so the list order follows the new numbers
function swapPositions<T extends { id: string; position: number }>(
  items: T[],
  index: number,
  delta: -1 | 1,
): [{ id: string; position: number }, { id: string; position: number }] | null {
  const target = items[index + delta];
  if (!target) return null;
  return [
    { id: items[index].id, position: target.position },
    { id: target.id, position: items[index].position },
  ];
}

export function StatusSection({
  projectId,
  statuses,
  busy,
  onRun,
  onDelete,
  onRename,
  onCategoryChange,
}: {
  projectId: string;
  statuses: ProjectStatus[];
  busy: boolean;
  onRun: (action: () => Promise<unknown>) => void;
  onDelete: (status: ProjectStatus) => void;
  // Each asks the page to confirm before the change is saved
  onRename: (status: ProjectStatus, name: string) => void;
  onCategoryChange: (status: ProjectStatus, category: StatusCategory) => void;
}) {
  const [name, setName] = useState("");
  const [category, setCategory] = useState<StatusCategory>("todo");
  const [error, setError] = useState<string | null>(null);

  const add = () => {
    if (!name.trim()) {
      setError("Name is required");
      return;
    }
    setError(null);
    onRun(() => createStatus(projectId, { name: name.trim(), category }));
    setName("");
  };

  const move = (index: number, delta: -1 | 1) => {
    const pair = swapPositions(statuses, index, delta);
    if (!pair) return;
    onRun(async () => {
      for (const change of pair) {
        await updateStatus(change.id, { position: change.position });
      }
    });
  };

  const changeCategory = (status: ProjectStatus, next: StatusCategory) => {
    if (next !== status.category) onCategoryChange(status, next);
  };

  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold">Statuses</h2>
      <p className="text-sm text-gray-600">
        Work items move through these in order. The category decides how a
        status counts on boards and reports.
      </p>
      <ul className="divide-y divide-gray-200 rounded border border-gray-200">
        {statuses.map((status, index) => (
          <li
            key={status.id}
            className="flex flex-wrap items-center justify-between gap-3 p-3"
          >
            <RenameStatus
              status={status}
              busy={busy}
              onRename={(name) => onRename(status, name)}
            />
            <div className="flex flex-wrap items-center gap-2">
              <label className="sr-only" htmlFor={`cat-${status.id}`}>
                Category of {status.name}
              </label>
              <select
                id={`cat-${status.id}`}
                value={status.category}
                disabled={busy}
                onChange={(e) =>
                  changeCategory(status, e.target.value as StatusCategory)
                }
                className={FIELD}
              >
                {(Object.keys(CATEGORY_LABELS) as StatusCategory[]).map((c) => (
                  <option key={c} value={c}>
                    {CATEGORY_LABELS[c]}
                  </option>
                ))}
              </select>
              <ReorderButtons
                index={index}
                count={statuses.length}
                disabled={busy}
                onMove={(delta) => move(index, delta)}
              />
              <button
                type="button"
                disabled={busy}
                onClick={() => onDelete(status)}
                className={DANGER}
              >
                Delete {status.name}
              </button>
            </div>
          </li>
        ))}
      </ul>

      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label htmlFor="new-status" className="block text-sm font-medium">
            New status
          </label>
          <input
            id="new-status"
            value={name}
            disabled={busy}
            onChange={(e) => setName(e.target.value)}
            className={FIELD}
          />
        </div>
        <div>
          <label
            htmlFor="new-status-category"
            className="block text-sm font-medium"
          >
            Category
          </label>
          <select
            id="new-status-category"
            value={category}
            disabled={busy}
            onChange={(e) => setCategory(e.target.value as StatusCategory)}
            className={FIELD}
          >
            {(Object.keys(CATEGORY_LABELS) as StatusCategory[]).map((c) => (
              <option key={c} value={c}>
                {CATEGORY_LABELS[c]}
              </option>
            ))}
          </select>
        </div>
        <button type="button" disabled={busy} onClick={add} className={PRIMARY}>
          Add status
        </button>
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </section>
  );
}

// A status name that can be changed; the page confirms the rename first
function RenameStatus({
  status,
  busy,
  onRename,
}: {
  status: ProjectStatus;
  busy: boolean;
  onRename: (name: string) => void;
}) {
  const [name, setName] = useState(status.name);
  const changed = name.trim() !== status.name && name.trim() !== "";
  return (
    <div className="flex items-center gap-2">
      <label className="sr-only" htmlFor={`name-${status.id}`}>
        Name of {status.name}
      </label>
      <input
        id={`name-${status.id}`}
        value={name}
        disabled={busy}
        onChange={(e) => setName(e.target.value)}
        className={FIELD}
      />
      <button
        type="button"
        disabled={busy || !changed}
        onClick={() => onRename(name.trim())}
        className="rounded border border-gray-300 px-3 py-1 text-sm hover:bg-gray-50 disabled:text-gray-300"
      >
        Rename
      </button>
    </div>
  );
}

export function TypeSection({
  projectId,
  types,
  busy,
  onRun,
  onDelete,
}: {
  projectId: string;
  types: WorkItemType[];
  busy: boolean;
  onRun: (action: () => Promise<unknown>) => void;
  onDelete: (type: WorkItemType) => void;
}) {
  const [name, setName] = useState("");
  const [level, setLevel] = useState<TypeLevel>("standard");
  const [error, setError] = useState<string | null>(null);

  const add = () => {
    if (!name.trim()) {
      setError("Name is required");
      return;
    }
    setError(null);
    onRun(() => createWorkItemType(projectId, { name: name.trim(), level }));
    setName("");
  };

  const move = (index: number, delta: -1 | 1) => {
    const pair = swapPositions(types, index, delta);
    if (!pair) return;
    onRun(async () => {
      for (const change of pair) {
        await updateWorkItemType(change.id, { position: change.position });
      }
    });
  };

  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold">Work item types</h2>
      <p className="text-sm text-gray-600">
        The level decides parent and subtask rules. A type's level can't change
        while work items use it.
      </p>
      <ul className="divide-y divide-gray-200 rounded border border-gray-200">
        {types.map((type, index) => (
          <li
            key={type.id}
            className="flex flex-wrap items-center justify-between gap-3 p-3"
          >
            <span className="font-medium">{type.name}</span>
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm text-gray-600">
                {LEVEL_LABELS[type.level]}
              </span>
              <ReorderButtons
                index={index}
                count={types.length}
                disabled={busy}
                onMove={(delta) => move(index, delta)}
              />
              <button
                type="button"
                disabled={busy}
                onClick={() => onDelete(type)}
                className={DANGER}
              >
                Delete {type.name}
              </button>
            </div>
          </li>
        ))}
      </ul>

      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label htmlFor="new-type" className="block text-sm font-medium">
            New type
          </label>
          <input
            id="new-type"
            value={name}
            disabled={busy}
            onChange={(e) => setName(e.target.value)}
            className={FIELD}
          />
        </div>
        <div>
          <label htmlFor="new-type-level" className="block text-sm font-medium">
            Level
          </label>
          <select
            id="new-type-level"
            value={level}
            disabled={busy}
            onChange={(e) => setLevel(e.target.value as TypeLevel)}
            className={FIELD}
          >
            <option value="standard">Standard</option>
            <option value="subtask">Subtask</option>
          </select>
        </div>
        <button type="button" disabled={busy} onClick={add} className={PRIMARY}>
          Add type
        </button>
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </section>
  );
}

export function TransitionSection({
  projectId,
  statuses,
  transitions,
  busy,
  onRun,
}: {
  projectId: string;
  statuses: ProjectStatus[];
  transitions: StatusTransition[];
  busy: boolean;
  onRun: (action: () => Promise<unknown>) => void;
}) {
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const nameOf = (id: string) =>
    statuses.find((status) => status.id === id)?.name ?? "Unknown status";

  const add = () => {
    if (!from || !to) return;
    onRun(() => createTransition(projectId, from, to));
  };

  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold">Transitions</h2>
      <p className="text-sm text-gray-600">
        {transitions.length === 0
          ? "No transitions: work items can move between any two statuses."
          : "Work items can only move along these transitions. Other moves are refused."}
      </p>
      <ul className="divide-y divide-gray-200 rounded border border-gray-200">
        {transitions.map((transition) => (
          <li
            key={transition.id}
            className="flex items-center justify-between gap-3 p-3"
          >
            <span>
              {nameOf(transition.from_status_id)} →{" "}
              {nameOf(transition.to_status_id)}
            </span>
            <button
              type="button"
              disabled={busy}
              onClick={() => onRun(() => deleteTransition(transition.id))}
              className={DANGER}
            >
              Remove
            </button>
          </li>
        ))}
      </ul>

      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label
            htmlFor="transition-from"
            className="block text-sm font-medium"
          >
            From
          </label>
          <select
            id="transition-from"
            value={from}
            disabled={busy}
            onChange={(e) => setFrom(e.target.value)}
            className={FIELD}
          >
            <option value="">Choose…</option>
            {statuses.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="transition-to" className="block text-sm font-medium">
            To
          </label>
          <select
            id="transition-to"
            value={to}
            disabled={busy}
            onChange={(e) => setTo(e.target.value)}
            className={FIELD}
          >
            <option value="">Choose…</option>
            {statuses.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>
        <button
          type="button"
          disabled={busy || !from || !to}
          onClick={add}
          className={PRIMARY}
        >
          Add transition
        </button>
      </div>
    </section>
  );
}
