import { useState } from "react";
import { WorkItemList } from "./WorkItemList";

// Keeps the selection in state the way the admin page does, and shows it for tests
export function WorkItemListSelection({
  onChange,
}: {
  onChange: (ids: string[]) => void;
}) {
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [total, setTotal] = useState(0);
  const update = (next: Set<string>) => {
    setSelected(next);
    onChange([...next]);
  };
  return (
    <>
      <span data-testid="selected">{[...selected].join(",")}</span>
      <span data-testid="total">{total}</span>
      <WorkItemList
        selection={{ selected, onChange: update }}
        onTotalChange={setTotal}
      />
    </>
  );
}
