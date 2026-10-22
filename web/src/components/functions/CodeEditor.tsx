import { markdown } from "@codemirror/lang-markdown";
import { python } from "@codemirror/lang-python";
import CodeMirror, { EditorView } from "@uiw/react-codemirror";
import { useLayoutEffect, useMemo, useRef, useState } from "react";
import { useTheme } from "../../lib/theme";

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
  grow = false,
  stretch = false,
  language = "python",
}: {
  value: string;
  onChange?: (value: string) => void;
  readOnly?: boolean;
  ariaLabel: string;
  placeholder?: string;
  // Caps the editor at the space left in the window instead of a fixed height.
  fill?: boolean;
  // Lets the editor grow with its content instead of scrolling past a max height.
  grow?: boolean;
  // Fills the height of a flex parent instead of using its own height.
  stretch?: boolean;
  language?: "python" | "markdown";
}) {
  const { theme } = useTheme();

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
    <div
      ref={wrapperRef}
      className={stretch ? "flex min-h-0 flex-1 flex-col" : undefined}
    >
      <CodeMirror
        value={value}
        onChange={onChange}
        extensions={extensions}
        theme={theme}
        placeholder={placeholder}
        readOnly={readOnly}
        editable={!readOnly}
        height={stretch ? "100%" : undefined}
        minHeight="12rem"
        maxHeight={grow ? undefined : fill ? fillHeight : DEFAULT_MAX_HEIGHT}
        className={`overflow-hidden rounded border border-border-strong font-mono text-sm ${stretch ? "min-h-0 flex-1" : ""}`}
      />
    </div>
  );
}
