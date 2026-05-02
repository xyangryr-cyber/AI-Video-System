// [SPEC-F-012] TimelineAnnotation — M-key annotation for task_ledger.
// Creates user_annotation entries with params={frame, time_sec, text}.

import { useState, useCallback, type FC, type KeyboardEvent } from "react";

export interface UserAnnotation {
  task_type: "user_annotation";
  params: {
    frame: number;
    time_sec: number;
    text: string;
  };
  /** Timestamp when the annotation was created */
  created_at: string;
}

export interface TimelineAnnotationProps {
  /** Current frame number */
  currentFrame: number;
  /** Frames per second for time conversion */
  fps: number;
  /** Callback when an annotation is created */
  onAnnotation?: (annotation: UserAnnotation) => void;
}

/**
 * TimelineAnnotation component for M-key annotation workflow.
 * Press M to open annotation input, type text, press Enter to confirm.
 * Creates a task_ledger entry with task_type=user_annotation.
 */
const TimelineAnnotation: FC<TimelineAnnotationProps> = ({ currentFrame, fps, onAnnotation }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [text, setText] = useState("");

  const timeSec = currentFrame / fps;

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "m" && !isOpen && !e.shiftKey && !e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        setIsOpen(true);
        setText("");
        return;
      }

      if (e.key === "Enter" && isOpen) {
        e.preventDefault();
        const annotation: UserAnnotation = {
          task_type: "user_annotation",
          params: {
            frame: currentFrame,
            time_sec: Math.round(timeSec * 1000) / 1000,
            text: text.trim() || `Annotation at frame ${currentFrame}`,
          },
          created_at: new Date().toISOString(),
        };
        onAnnotation?.(annotation);
        setIsOpen(false);
        setText("");
        return;
      }

      if (e.key === "Escape" && isOpen) {
        setIsOpen(false);
        setText("");
      }
    },
    [isOpen, currentFrame, timeSec, text, onAnnotation],
  );

  if (!isOpen) {
    return (
      <div
        className="timeline-annotation-indicator"
        style={{
          position: "absolute",
          bottom: 4,
          left: 4,
          color: "rgba(255,255,255,0.4)",
          fontSize: 10,
          fontFamily: "monospace",
        }}
        onKeyDown={handleKeyDown}
        tabIndex={0}
      >
        M to annotate @ frame {currentFrame}
      </div>
    );
  }

  return (
    <div
      className="timeline-annotation-input"
      style={{
        position: "absolute",
        bottom: "10%",
        left: "50%",
        transform: "translateX(-50%)",
        zIndex: 100,
      }}
      onKeyDown={handleKeyDown}
    >
      <input
        autoFocus
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={`Annotate frame ${currentFrame} (Enter to save)`}
        style={{
          padding: "8px 12px",
          fontSize: 14,
          borderRadius: 4,
          border: "1px solid #555",
          backgroundColor: "#1a1a2e",
          color: "#fff",
          width: 300,
        }}
      />
    </div>
  );
};

export default TimelineAnnotation;
