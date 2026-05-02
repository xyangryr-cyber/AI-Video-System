// [SPEC-A-103] StoryboardShotAnchor cross-language contract.
// Mirror of src/shared/schemas/storyboard_shot_anchor.py.
// Authority: docs/specs/SPEC-A-contracts.md §A-BDD-4 (SPEC-0A.12).

export interface DownstreamBindings {
  p8_template_shot_id?: string;
  p9_broll_shot_id?: string;
  p10_track_ref?: string;
}

export interface StoryboardShotAnchor {
  shot_id: string;
  anchor_text: string;
  script_span_id: string;
  start_char: number;
  end_char: number;
  split_from_shot_id?: string;
  downstream_bindings: DownstreamBindings;
}
