// Remotion TemplateProps contract (SPEC-0A.7).
// Mirror of src/shared/schemas/template_props.py.

import type { ChartMaterial } from "./chart_material";
import type {
  AnnotationKeyframe,
  ContinuousKeyframe,
  DiscreteKeyframe,
  ThemeConfig,
} from "./shared_types";

export interface TimelineSegmentRange {
  startFrame: number;
  endFrame: number;
}

export interface TemplateProps {
  templateId: string;
  data: unknown;
  annotationKeyframes: (DiscreteKeyframe | ContinuousKeyframe)[];
  timelineSegment: TimelineSegmentRange;
  theme: ThemeConfig;
  fps: number;
  /** v3.17: optional chart_material from P7A — chart templates consume this
   *  preferentially over free-form `data`. When absent (v3.15/v3.16 callers),
   *  rendering falls back to `data` with zero breaking change. */
  chart_material?: ChartMaterial;
}

// Re-exported for convenience of downstream template code that only wants
// the union alias.
export type { AnnotationKeyframe };
