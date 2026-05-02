import { type ReactElement, useRef, useEffect } from "react";
import { ShotSplitter } from "./ShotSplitter";

export interface ScriptPaneAnchor {
  start: number;
  end: number;
  shotId: string;
}

export interface ScriptPaneProps {
  script: string;
  selectedAnchor?: ScriptPaneAnchor;
  splitOffset?: number;
  onSplit?: (offset: number) => void;
}

export function ScriptPane({
  script,
  selectedAnchor,
  splitOffset,
  onSplit,
}: ScriptPaneProps): ReactElement {
  const highlightRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (highlightRef.current && typeof highlightRef.current.scrollIntoView === "function") {
      highlightRef.current.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }
  }, [selectedAnchor]);

  if (!selectedAnchor) {
    return (
      <div
        data-testid="script-pane"
        style={{
          padding: "12px",
          whiteSpace: "pre-wrap",
          fontFamily: "monospace",
          fontSize: "14px",
          lineHeight: "1.6",
        }}
      >
        {script}
      </div>
    );
  }

  const { start, end } = selectedAnchor;

  const before = script.slice(0, start);
  const anchor = script.slice(start, end);
  const after = script.slice(end);

  const midOffset = Math.floor((start + end) / 2);
  const showSplitter = onSplit && splitOffset !== undefined;

  return (
    <div
      data-testid="script-pane"
      style={{
        padding: "12px",
        whiteSpace: "pre-wrap",
        fontFamily: "monospace",
        fontSize: "14px",
        lineHeight: "1.6",
      }}
    >
      {before}
      <span
        ref={highlightRef}
        data-testid="anchor-highlight"
        style={{ backgroundColor: "#fef08a", borderRadius: "2px" }}
      >
        {anchor}
        {showSplitter && (
          <ShotSplitter
            splitOffset={splitOffset ?? midOffset - start}
            onSplit={(offset) => onSplit(offset + start)}
          />
        )}
      </span>
      {after}
    </div>
  );
}
