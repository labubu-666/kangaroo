import { useNavigate } from "@tanstack/react-router";
import { useGoBackOr } from "../lib/navigation";
import { projectFilter } from "../lib/filter-bubbles";

// Test-only button that calls useGoBackOr with a fallback chosen by `target`
export function GoBackOrButton({
  label,
  target,
  projectId,
}: {
  label: string;
  target: "list" | "item";
  projectId?: string;
}) {
  const navigate = useNavigate();
  const goBackOr = useGoBackOr();
  return (
    <button
      onClick={() =>
        goBackOr(() =>
          target === "list"
            ? navigate({
                to: "/work-items",
                search: { filter: projectFilter(projectId) },
              })
            : navigate({ to: "/work-items/$id", params: { id: "1" } }),
        )
      }
    >
      {label}
    </button>
  );
}
