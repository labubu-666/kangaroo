import { useRef, useState } from "react";
import type { Project } from "../../lib/projects";

// Shows this many projects before the user types a search
const PROJECT_PICKER_LIMIT = 3;

// Matches a project by name or ID, ignoring case. An empty search matches all.
function matchProjects(projects: Project[], search: string): Project[] {
  const needle = search.trim().toLowerCase();
  if (!needle) return projects;
  return projects.filter(
    (project) =>
      project.name.toLowerCase().includes(needle) ||
      project.id.toLowerCase().includes(needle),
  );
}

// Picks a project by name. `value` is the project ID or name, depending on
// the field, and is what gets written into the filter.
export function ProjectPicker({
  value,
  projects,
  useId,
  onChange,
}: {
  value: string;
  projects: Project[];
  useId: boolean;
  onChange: (value: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const buttonRef = useRef<HTMLButtonElement>(null);

  const valueOf = (project: Project) => (useId ? project.id : project.name);
  const selected = projects.find((project) => valueOf(project) === value);
  const label = selected?.name ?? value;

  const matches = matchProjects(projects, search);
  // With no search, show only the first few projects
  const shown = search.trim()
    ? matches
    : matches.slice(0, PROJECT_PICKER_LIMIT);
  const hidden = matches.length - shown.length;

  const close = () => {
    setOpen(false);
    setSearch("");
    buttonRef.current?.focus();
  };

  const choose = (project: Project) => {
    onChange(valueOf(project));
    close();
  };

  return (
    <div className="relative">
      <button
        ref={buttonRef}
        type="button"
        aria-label="Value"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((isOpen) => !isOpen)}
        className="min-w-[10rem] rounded border border-gray-300 bg-white px-2 py-0.5 text-left text-sm text-gray-800"
      >
        {label || "Choose a project"}
      </button>
      {open && (
        <div
          onKeyDown={(e) => {
            if (e.key === "Escape") close();
          }}
          className="absolute left-0 z-10 mt-1 w-64 rounded border border-gray-200 bg-white p-2 shadow-md"
        >
          <input
            aria-label="Search projects"
            type="text"
            value={search}
            placeholder="Search projects"
            autoFocus
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded border border-gray-300 px-2 py-1 text-sm"
          />
          <ul role="listbox" className="mt-2 flex flex-col">
            {shown.map((project) => (
              <li
                key={project.id}
                role="option"
                aria-selected={valueOf(project) === value}
              >
                <button
                  type="button"
                  onClick={() => choose(project)}
                  className="w-full rounded px-2 py-1 text-left text-sm hover:bg-blue-50"
                >
                  {project.name}
                </button>
              </li>
            ))}
          </ul>
          {shown.length === 0 && (
            <p className="px-2 py-1 text-sm text-gray-500">No projects match</p>
          )}
          {hidden > 0 && (
            <p className="px-2 pt-1 text-xs text-gray-500">
              {hidden} more, type to search
            </p>
          )}
        </div>
      )}
    </div>
  );
}
