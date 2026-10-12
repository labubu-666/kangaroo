import { CopyBase } from "./CopyBase";

export function CopyFilter({ filter }: { filter: string }) {
  return (
    <CopyBase value={filter} ariaLabel="Copy filter" title="Copy filter" />
  );
}
