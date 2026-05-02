"""[SPEC-C-020] SfxReviewerOrchestrator routing tests.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-5.

Covers:
  AC-3: layout problems never invoke MixReviewer; mix problems never
        invoke LayoutReviewer (isolation via spy subclasses).
  AC-5: mix_feedback dispatches only the segment-remix callback;
        layout_feedback dispatches only the full-relayout callback.
  AC-7: orchestrator branch coverage — both routes fire end-to-end.
"""

from __future__ import annotations

from typing import Any

import numpy as np


def _trigger(
    trigger_id: str = "trg_001",
    planned_time_sec: float = 5.0,
    duration_seconds: float = 0.3,
    rationale: str = "emphasis",
    narrative_role: str = "climax",
) -> Any:
    from src.shared.schemas.sfx_layout_plan import (
        SfxLayoutTrigger,
        SfxScriptAnchor,
    )

    return SfxLayoutTrigger(
        trigger_id=trigger_id,
        script_anchor=SfxScriptAnchor(span_id="span_01", text="hook"),
        keyword_span=[0, 4],
        planned_time_sec=planned_time_sec,
        sfx_type="whoosh",
        rationale=rationale,
        narrative_role=narrative_role,
        volume_db=0.0,
        duration_seconds=duration_seconds,
    )


def _plan(triggers: list) -> Any:
    from src.shared.schemas.sfx_layout_plan import SfxLayoutPlan

    return SfxLayoutPlan(plan_version=1, triggers=triggers)


def _sine(sr: int, secs: float, freq: float, amp: float = 0.3) -> np.ndarray:
    t = np.arange(int(sr * secs)) / sr
    return (amp * np.sin(2 * np.pi * freq * t)).astype(np.float64)


# ---------- AC-3 --------------------------------------------------------


class TestAC3LayoutProblemIsolated:
    def test_layout_problem_isolated(self) -> None:
        from src.backend.reviewers.sfx_layout_reviewer import SfxLayoutReviewer
        from src.backend.reviewers.sfx_mix_reviewer import SfxMixReviewer
        from src.backend.reviewers.sfx_reviewer_orchestrator import (
            SfxReviewerOrchestrator,
        )

        mix_calls: list[str] = []

        class _SpyMix(SfxMixReviewer):
            def review(self, **kw: Any) -> Any:  # type: ignore[override]
                mix_calls.append("review")
                return super().review(**kw)

        orch = SfxReviewerOrchestrator(
            layout_reviewer=SfxLayoutReviewer(), mix_reviewer=_SpyMix()
        )
        bad_plan = _plan(
            [_trigger("trg_001", rationale="   ", narrative_role="climax")]
        )
        script_nodes = [{"narrative_role": "climax", "time_sec": 5.0}]
        report = orch.review_layout(
            plan=bad_plan, script_nodes=script_nodes, script_text=""
        )
        assert report.verdict == "FAIL"
        assert mix_calls == [], "MixReviewer invoked during layout review"


class TestAC3MixProblemIsolated:
    def test_mix_problem_isolated(self) -> None:
        from src.backend.reviewers.sfx_layout_reviewer import SfxLayoutReviewer
        from src.backend.reviewers.sfx_mix_reviewer import SfxMixReviewer
        from src.backend.reviewers.sfx_reviewer_orchestrator import (
            SfxReviewerOrchestrator,
        )

        layout_calls: list[str] = []

        class _SpyLayout(SfxLayoutReviewer):
            def review(self, **kw: Any) -> Any:  # type: ignore[override]
                layout_calls.append("review")
                return super().review(**kw)

        orch = SfxReviewerOrchestrator(
            layout_reviewer=_SpyLayout(), mix_reviewer=SfxMixReviewer()
        )
        sr = 44100
        clipped = _sine(sr, 0.5, 440.0, amp=0.3)
        clipped[100:200] = 1.0
        narration = _sine(sr, 0.5, 300.0, amp=0.3)
        bgm = _sine(sr, 0.5, 440.0, amp=0.3)
        report = orch.review_mix(
            segment_audio=clipped,
            narration=narration,
            bgm=bgm,
            sr=sr,
        )
        assert report.verdict == "FAIL"
        assert layout_calls == [], "LayoutReviewer invoked during mix review"


# ---------- AC-5 --------------------------------------------------------


class TestAC5MixFeedbackPartialRemix:
    def test_mix_feedback_partial_remix(self) -> None:
        from src.backend.reviewers.sfx_reviewer_orchestrator import (
            SfxReviewerOrchestrator,
        )
        from src.shared.schemas.feedback_protocol import SfxReviewerFeedback

        orch = SfxReviewerOrchestrator()
        layout_calls: list[Any] = []
        segment_calls: list[Any] = []

        fb = SfxReviewerFeedback(
            comment_type="mix_feedback",
            target="seg_03",
            action="modify",
            payload={"volume_db": -3.0},
        )
        decision = orch.dispatch(
            fb,
            on_layout_replan=lambda f: layout_calls.append(f),
            on_segment_remix=lambda f: segment_calls.append(f),
        )
        assert decision == "segment_remix"
        assert layout_calls == []
        assert [f.target for f in segment_calls] == ["seg_03"]


class TestAC5LayoutFeedbackFullRelayout:
    def test_layout_feedback_full_relayout(self) -> None:
        from src.backend.reviewers.sfx_reviewer_orchestrator import (
            SfxReviewerOrchestrator,
        )
        from src.shared.schemas.feedback_protocol import SfxReviewerFeedback

        orch = SfxReviewerOrchestrator()
        layout_calls: list[Any] = []
        segment_calls: list[Any] = []

        fb = SfxReviewerFeedback(
            comment_type="layout_feedback",
            target="trg_001",
            action="remove",
            payload={},
        )
        decision = orch.dispatch(
            fb,
            on_layout_replan=lambda f: layout_calls.append(f),
            on_segment_remix=lambda f: segment_calls.append(f),
        )
        assert decision == "layout_replan"
        assert segment_calls == []
        assert [f.target for f in layout_calls] == ["trg_001"]


# ---------- AC-7 --------------------------------------------------------


class TestAC7OrchestratorBranchCoverage:
    def test_orchestrator_branch_coverage(self) -> None:
        from src.backend.reviewers.sfx_reviewer_orchestrator import (
            SfxReviewerOrchestrator,
        )
        from src.shared.schemas.feedback_protocol import SfxReviewerFeedback

        orch = SfxReviewerOrchestrator()
        layout_hits: list[str] = []
        segment_hits: list[str] = []

        for fb in [
            SfxReviewerFeedback(
                comment_type="layout_feedback",
                target="trg_010",
                action="modify",
                payload={},
            ),
            SfxReviewerFeedback(
                comment_type="mix_feedback",
                target="seg_07",
                action="modify",
                payload={},
            ),
        ]:
            orch.dispatch(
                fb,
                on_layout_replan=lambda f: layout_hits.append(f.target),
                on_segment_remix=lambda f: segment_hits.append(f.target),
            )

        assert layout_hits == ["trg_010"]
        assert segment_hits == ["seg_07"]
