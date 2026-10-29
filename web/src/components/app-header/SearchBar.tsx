import { Link, useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useId, useState, type KeyboardEvent } from "react";
import { searchAll } from "../../lib/search";

const MIN_CHARS = 2;
const DEBOUNCE_MS = 250;
const SUGGESTIONS_PER_TYPE = 3;

interface Suggestion {
  key: string;
  label: string;
  group: string;
  to: string;
  params: { id: string; boardId?: string };
}

export function SearchBar() {
  const [text, setText] = useState("");
  const [term, setTerm] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const navigate = useNavigate();
  const listId = useId();

  // Wait for typing to pause before searching
  useEffect(() => {
    const trimmed = text.trim();
    const timer = setTimeout(
      () => setTerm(trimmed.length >= MIN_CHARS ? trimmed : ""),
      DEBOUNCE_MS,
    );
    return () => clearTimeout(timer);
  }, [text]);

  const { data } = useQuery({
    queryKey: ["search", term],
    queryFn: () => searchAll(term, SUGGESTIONS_PER_TYPE),
    enabled: term !== "",
  });

  const suggestions: Suggestion[] = data
    ? [
        ...data.workItems.results.map((item) => ({
          key: `work-${item.id}`,
          label: item.summary,
          group: "Work items",
          to: "/work-items/$id",
          params: { id: item.id },
        })),
        ...data.projects.results.map((project) => ({
          key: `project-${project.id}`,
          label: project.name,
          group: "Projects",
          to: "/projects/$id",
          params: { id: project.id },
        })),
        ...data.boards.results.map((board) => ({
          key: `board-${board.id}`,
          label: board.name,
          group: "Boards",
          to: "/projects/$id/boards/$boardId",
          params: { id: board.project_id, boardId: board.id },
        })),
      ]
    : [];

  const showList = open && term !== "" && suggestions.length > 0;

  const goToResults = () => {
    const q = text.trim();
    if (q.length === 0) return;
    setOpen(false);
    navigate({ to: "/search", search: { q } });
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setOpen(true);
      setActive((i) => Math.min(i + 1, suggestions.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((i) => Math.max(i - 1, -1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      const picked = showList ? suggestions[active] : undefined;
      if (picked) {
        setOpen(false);
        navigate({ to: picked.to, params: picked.params });
      } else {
        goToResults();
      }
    } else if (e.key === "Escape") {
      setOpen(false);
      setActive(-1);
    }
  };

  return (
    <div
      className="relative min-w-0 flex-1 basis-48"
      onBlur={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget)) setOpen(false);
      }}
    >
      <form
        role="search"
        onSubmit={(e) => {
          e.preventDefault();
          goToResults();
        }}
      >
        <input
          type="search"
          role="combobox"
          aria-label="Search"
          aria-expanded={showList}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={
            showList && active >= 0 ? `${listId}-${active}` : undefined
          }
          placeholder="Search work items, projects and boards"
          value={text}
          onChange={(e) => {
            setText(e.target.value);
            setOpen(true);
            setActive(-1);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={handleKeyDown}
          className="block h-8 w-full rounded border border-border-strong px-3 py-1.5 text-sm"
        />
      </form>

      {showList && (
        <ul
          id={listId}
          role="listbox"
          aria-label="Search suggestions"
          className="absolute left-0 right-0 z-10 mt-1 max-h-96 overflow-auto rounded border border-border bg-surface py-1 shadow-lg"
        >
          {suggestions.map((s, index) => (
            <li
              key={s.key}
              id={`${listId}-${index}`}
              role="option"
              aria-selected={index === active}
              onMouseDown={(e) => e.preventDefault()}
              className={`px-3 py-2 text-sm ${
                index === active ? "bg-primary-subtle" : ""
              }`}
            >
              <Link
                to={s.to}
                params={s.params}
                tabIndex={-1}
                onClick={() => setOpen(false)}
                className="flex items-center justify-between gap-2 hover:underline"
              >
                <span className="truncate">{s.label}</span>
                <span className="shrink-0 text-xs text-fg-muted">
                  {s.group}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
