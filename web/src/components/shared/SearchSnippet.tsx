import { Highlight } from "./Highlight";
import type { SearchHit } from "../../lib/search";

// Shows the text around a search hit, with the matches highlighted
export function SearchSnippet({
  hit,
  term,
}: {
  hit: SearchHit | null;
  term: string;
}) {
  if (!hit) return null;
  const more = hit.match_count - 1;
  return (
    <p className="text-sm text-fg-secondary">
      <Highlight text={hit.text} term={term} />
      {more > 0 && (
        <span className="ml-2 text-fg-muted">
          +{more} more {more === 1 ? "match" : "matches"}
        </span>
      )}
    </p>
  );
}
