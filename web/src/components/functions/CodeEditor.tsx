import { markdown } from "@codemirror/lang-markdown";
import { python } from "@codemirror/lang-python";
import CodeMirror, { EditorView } from "@uiw/react-codemirror";
import { useLayoutEffect, useMemo, useRef, useState } from "react";

// Space kept free below the editor for the footer and page padding.
const FILL_RESERVE_PX = 120;
const DEFAULT_MAX_HEIGHT = "24rem";

export function CodeEditor({
  value,
  onChange,
  readOnly = false,
  ariaLabel,
  placeholder,
  fill = false,
  language = "python",
}: {
  value: string;
  onChange?: (value: string) => void;
  readOnly?: boolean;
  ariaLabel: string;
  placeholder?: string;
  // Caps the editor at the space left in the window instead of a fixed height.
  fill?: boolean;
  language?: "python" | "markdown";
}) {
  // Memoized so CodeMirror does not reconfigure the editor on every render.
  const extensions = useMemo(
    () => [
      language === "markdown" ? markdown() : python(),
      EditorView.contentAttributes.of({ "aria-label": ariaLabel }),
    ],
    [ariaLabel, language],
  );

  // A parent with no height limit lets the editor grow forever, so the limit is
  // measured from where the editor starts on screen.
  const wrapperRef = useRef<HTMLDivElement>(null);
  const [fillHeight, setFillHeight] = useState<string | undefined>();

  useLayoutEffect(() => {
    if (!fill) return;
    const measure = () => {
      const top = wrapperRef.current?.getBoundingClientRect().top ?? 0;
      const available = window.innerHeight - top - FILL_RESERVE_PX;
      setFillHeight(`${Math.max(available, 192)}px`);
    };
    measure();
    window.addEventListener("resize", measure);
    return () => window.removeEventListener("resize", measure);
  }, [fill]);

  return (
    <div ref={wrapperRef}>
      <CodeMirror
        value={value}
        onChange={onChange}
        extensions={extensions}
        placeholder={placeholder}
        readOnly={readOnly}
        editable={!readOnly}
        minHeight="12rem"
        maxHeight={fill ? fillHeight : DEFAULT_MAX_HEIGHT}
        className="overflow-hidden rounded border border-gray-300 font-mono text-sm"
      />
    </div>
  );
}
