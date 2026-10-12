import { CopyBase } from "./CopyBase";

export function CopyId({
  id,
  url,
  display,
  prefix = "#",
}: {
  id: string;
  url: string;
  display?: string;
  prefix?: string;
}) {
  return (
    <CopyBase value={url} ariaLabel={`Copy link for ${id}`}>
      <span className="truncate">
        {prefix}
        {display ?? id}
      </span>
    </CopyBase>
  );
}
