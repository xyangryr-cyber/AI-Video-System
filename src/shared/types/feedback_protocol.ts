// [SPEC-C-020] SfxReviewerFeedback protocol (TypeScript mirror).
// Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-5.
//
// Target regex cross-check lives in the Python Pydantic model and the
// SfxReviewerOrchestrator; the TypeScript side documents the same
// invariant via the discriminated-union alias below.

export type CommentType = "layout_feedback" | "mix_feedback";
export type FeedbackAction = "add" | "remove" | "modify";

export interface SfxLayoutFeedback {
  comment_type: "layout_feedback";
  target: string; // ^trg_\d{3,}$
  action: FeedbackAction;
  payload: Record<string, unknown>;
}

export interface SfxMixFeedback {
  comment_type: "mix_feedback";
  target: string; // ^seg_\d{2,}$
  action: FeedbackAction;
  payload: Record<string, unknown>;
}

export type SfxReviewerFeedback = SfxLayoutFeedback | SfxMixFeedback;
