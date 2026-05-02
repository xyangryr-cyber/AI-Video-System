// [SPEC-A-014] SfxLayoutPlan types (TypeScript mirror).
// Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md A-AUDP7A-2.
//
// Keep in lockstep with src/shared/schemas/sfx_layout_plan.py and
// schemas/sfx_layout_plan.schema.json.

export interface SfxScriptAnchor {
  span_id: string;
  text: string;
}

export interface SfxLayoutTrigger {
  trigger_id: string; // ^trg_\d{3,}$
  script_anchor: SfxScriptAnchor;
  // Tuple [start, end] of character offsets in the script (both >= 0).
  keyword_span: [number, number];
  planned_time_sec: number; // >= 0
  sfx_type: string;
  rationale: string;
  narrative_role: string;
  volume_db: number;
  duration_seconds: number; // >= 0
}

export interface SfxLayoutPlan {
  plan_version: number; // >= 1
  triggers: SfxLayoutTrigger[];
}
