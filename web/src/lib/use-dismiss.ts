import { useEffect, useRef } from "react";

// Calls onDismiss when a click lands outside the returned ref, or Escape is
// pressed. Listeners are only attached while open, so closed menus cost nothing.
export function useDismiss<T extends HTMLElement>(
  open: boolean,
  onDismiss: () => void,
) {
  const ref = useRef<T>(null);

  useEffect(() => {
    if (!open) return;
    const handlePointerDown = (e: MouseEvent) => {
      if (!ref.current?.contains(e.target as Node)) onDismiss();
    };
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onDismiss();
    };
    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open, onDismiss]);

  return ref;
}
