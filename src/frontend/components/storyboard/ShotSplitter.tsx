import type { ReactElement } from "react";

/**
 * Calculate child shot durations when splitting a parent shot at a given character offset.
 * Durations are proportional to the character offset ratio within the anchor text.
 *
 * @returns [leftChildDuration, rightChildDuration] in seconds
 */
export function calcSplitDurations(
  parentDurationSec: number,
  anchorStart: number,
  anchorEnd: number,
  splitOffset: number,
): [number, number] {
  const anchorLen = anchorEnd - anchorStart;
  if (anchorLen <= 0) {
    return [parentDurationSec / 2, parentDurationSec / 2];
  }
  const relativeOffset = splitOffset - anchorStart;
  const leftRatio = relativeOffset / anchorLen;
  const leftDur = parentDurationSec * leftRatio;
  const rightDur = parentDurationSec - leftDur;
  return [leftDur, rightDur];
}

export interface ShotSplitterProps {
  splitOffset: number;
  onSplit: (offset: number) => void;
}

export function ShotSplitter({ splitOffset, onSplit }: ShotSplitterProps): ReactElement {
  return (
    <span
      data-testid="split-handle"
      role="button"
      tabIndex={0}
      onClick={() => onSplit(splitOffset)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          onSplit(splitOffset);
        }
      }}
      style={{
        display: "inline-block",
        width: "4px",
        height: "1.2em",
        backgroundColor: "#ef4444",
        cursor: "col-resize",
        verticalAlign: "middle",
        margin: "0 1px",
        borderRadius: "2px",
      }}
      aria-label="Split handle"
    />
  );
}
