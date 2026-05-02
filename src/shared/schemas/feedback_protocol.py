"""[SPEC-C-020] Sfx reviewer feedback protocol schema.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-5.

Feedback submitted through SfxLayoutReviewer / SfxMixReviewer carries a
``comment_type`` discriminator so the orchestrator can route the request
to either a full layout re-plan (``layout_feedback`` → trigger id) or a
partial per-segment remix (``mix_feedback`` → segment id). The target
kind is cross-checked against ``comment_type`` at validation time.

Keep in lockstep with ``src/shared/types/feedback_protocol.ts``.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


CommentType = Literal["layout_feedback", "mix_feedback"]
FeedbackAction = Literal["add", "remove", "modify"]

_TRIGGER_ID_RE = re.compile(r"^trg_\d{3,}$")
_SEGMENT_ID_RE = re.compile(r"^seg_\d{2,}$")


class SfxReviewerFeedback(BaseModel):
    """One feedback item routed through :class:`SfxReviewerOrchestrator`.

    Invariants (SPEC-C-020 AC-4):
      * ``comment_type`` is required and must be one of the two literals.
      * ``comment_type=layout_feedback`` ⇒ ``target`` matches ``trg_XXX``.
      * ``comment_type=mix_feedback`` ⇒ ``target`` matches ``seg_XX``.
    """

    model_config = ConfigDict(extra="forbid")

    comment_type: CommentType
    target: str = Field(min_length=1)
    action: FeedbackAction
    payload: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _target_matches_comment_type(self) -> "SfxReviewerFeedback":
        if self.comment_type == "layout_feedback":
            if not _TRIGGER_ID_RE.match(self.target):
                raise ValueError(
                    "layout_feedback.target must match trigger id "
                    f"pattern {_TRIGGER_ID_RE.pattern!r}; got {self.target!r}"
                )
        else:  # mix_feedback
            if not _SEGMENT_ID_RE.match(self.target):
                raise ValueError(
                    "mix_feedback.target must match segment id "
                    f"pattern {_SEGMENT_ID_RE.pattern!r}; got {self.target!r}"
                )
        return self


__all__ = [
    "CommentType",
    "FeedbackAction",
    "SfxReviewerFeedback",
]
