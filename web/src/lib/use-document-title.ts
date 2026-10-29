import { useEffect } from "react";

// Shows the page's own title in the browser tab; the app title returns when the page unmounts
export function useDocumentTitle(title: string | undefined) {
  useEffect(() => {
    if (!title) return;
    document.title = `${title} - kangaroo`;
    return () => {
      document.title = "kangaroo";
    };
  }, [title]);
}
