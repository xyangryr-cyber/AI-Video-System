// [SPEC-E-015] AnnotationSpan — frontend View type mirroring shared AnnotationSpan.
// Keep in lockstep with src/shared/types/artifacts.ts and SPEC-A-014.
export interface AnnotationSpan {
  span_id: string;
  text_range: [number, number];
  effect: string;
  rationale: string;
  narrative_role: string;
}
