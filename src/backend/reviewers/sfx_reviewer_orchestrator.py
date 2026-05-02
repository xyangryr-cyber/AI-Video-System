"""[SPEC-C-020] SfxReviewerOrchestrator — routing between
SfxLayoutReviewer and SfxMixReviewer.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-5.

Two responsibilities:

1. **Review routing** — ``review_layout`` only invokes
   :class:`SfxLayoutReviewer`; ``review_mix`` only invokes
   :class:`SfxMixReviewer`. The other side never runs, which is the
   isolation contract exercised in SPEC-C-020 AC-3.

2. **Feedback dispatch** — ``dispatch`` reads
   :class:`~src.shared.schemas.feedback_protocol.SfxReviewerFeedback`,
   and forwards ``layout_feedback`` to the injected layout-replan
   callable (Step 1 of the P6 loop) and ``mix_feedback`` to the
   segment-remix callable (only the affected segment). Returns
   ``"layout_replan"`` / ``"segment_remix"`` so callers can persist the
   routing decision without re-reading ``comment_type``.

The orchestrator keeps the two branches completely separate so the
incremental-redo contract (AC-5) and the 100% branch-coverage contract
(AC-7) are structural rather than runtime-dependent.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any, Literal

import numpy as np

from src.backend.reviewers.music_fit_reviewer import ReviewReport
from src.backend.reviewers.sfx_layout_reviewer import SfxLayoutReviewer
from src.backend.reviewers.sfx_mix_reviewer import SfxMixReviewer
from src.shared.schemas.feedback_protocol import SfxReviewerFeedback
from src.shared.schemas.sfx_layout_plan import SfxLayoutPlan

DispatchDecision = Literal["layout_replan", "segment_remix"]
FeedbackHandler = Callable[[SfxReviewerFeedback], Any]


class SfxReviewerOrchestrator:
    """Single entry point for both SFX reviewer layers + feedback routing."""

    def __init__(
        self,
        layout_reviewer: SfxLayoutReviewer | None = None,
        mix_reviewer: SfxMixReviewer | None = None,
    ) -> None:
        self._layout_reviewer = layout_reviewer or SfxLayoutReviewer()
        self._mix_reviewer = mix_reviewer or SfxMixReviewer()

    # -- Review routing (AC-3) ------------------------------------------

    def review_layout(
        self,
        *,
        plan: SfxLayoutPlan,
        script_nodes: Sequence[Mapping[str, Any]] | None = None,
        script_text: str = "",
    ) -> ReviewReport:
        return self._layout_reviewer.review(
            plan=plan,
            script_nodes=script_nodes,
            script_text=script_text,
        )

    def review_mix(
        self,
        *,
        segment_audio: np.ndarray,
        narration: np.ndarray,
        bgm: np.ndarray,
        sr: int,
        layout_context: Any = None,
    ) -> ReviewReport:
        return self._mix_reviewer.review(
            segment_audio=segment_audio,
            narration=narration,
            bgm=bgm,
            sr=sr,
            layout_context=layout_context,
        )

    # -- Feedback dispatch (AC-5 / AC-7) --------------------------------

    def dispatch(
        self,
        feedback: SfxReviewerFeedback,
        *,
        on_layout_replan: FeedbackHandler,
        on_segment_remix: FeedbackHandler,
    ) -> DispatchDecision:
        if feedback.comment_type == "layout_feedback":
            on_layout_replan(feedback)
            return "layout_replan"
        on_segment_remix(feedback)
        return "segment_remix"


__all__ = [
    "DispatchDecision",
    "FeedbackHandler",
    "SfxReviewerOrchestrator",
]
