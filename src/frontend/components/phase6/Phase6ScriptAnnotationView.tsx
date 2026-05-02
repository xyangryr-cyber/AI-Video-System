import { useState } from "react";
import type { ReactElement } from "react";
import type { AnnotationSpan } from "@frontend/types/annotation_span";

interface Props {
  fullText: string;
  annotationSpans: AnnotationSpan[];
  onConfirm: () => void;
}

export function Phase6ScriptAnnotationView({
  fullText,
  annotationSpans,
  onConfirm,
}: Props): ReactElement {
  const [hoveredSpan, setHoveredSpan] = useState<string | null>(null);

  const spansByPosition = new Map<string, AnnotationSpan[]>();
  for (const span of annotationSpans) {
    const key = `${span.text_range[0]}-${span.text_range[1]}`;
    const existing = spansByPosition.get(key) || [];
    existing.push(span);
    spansByPosition.set(key, existing);
  }

  return (
    <div data-testid="p6-annotation-view" className="border rounded p-4">
      <h3 className="text-sm font-medium mb-2">全文标注视图</h3>
      <p className="text-sm leading-relaxed mb-4">
        {Array.from(spansByPosition.entries()).length > 0
          ? "annotated"
          : fullText}
      </p>

      <div className="space-y-2">
        {Array.from(spansByPosition.entries()).map(([_posKey, group]) => {
          const span = group[0];
          const isStacked = group.length > 1;
          const tooltipId = `tooltip-${span.span_id}`;

          return (
            <div
              key={span.span_id}
              data-testid="annotation-highlight"
              aria-describedby={tooltipId}
              className="relative bg-yellow-100 border-l-4 border-yellow-400 px-2 py-1 text-xs inline-flex items-center gap-1"
              onMouseEnter={() => setHoveredSpan(span.span_id)}
              onMouseLeave={() => setHoveredSpan(null)}
            >
              <span>
                [{span.text_range[0]}-{span.text_range[1]}] {span.effect}
              </span>
              {isStacked && (
                <span
                  data-testid="stacked-badge"
                  className="bg-blue-500 text-white rounded-full w-4 h-4 text-xs flex items-center justify-center"
                >
                  {group.length}
                </span>
              )}
              {hoveredSpan === span.span_id && (
                <div
                  id={tooltipId}
                  role="tooltip"
                  className="absolute top-full left-0 mt-1 bg-gray-800 text-white text-xs rounded px-2 py-1 z-10"
                >
                  <div>rationale: {span.rationale}</div>
                  <div>narrative_role: {span.narrative_role}</div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <button
        aria-label="确认布局"
        className="mt-4 px-3 py-1 text-sm border rounded"
        onClick={onConfirm}
      >
        确认布局
      </button>
    </div>
  );
}
