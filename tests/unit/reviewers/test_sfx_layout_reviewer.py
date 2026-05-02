"""[SPEC-C-020] SfxLayoutReviewer unit tests + feedback-protocol schema
+ v3.15 deprecated SFXReviewer regression.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-5.

Covers:
  AC-1: 4 L1 checks (script_coverage / keyword_anchor /
        explanation_completeness / sparsity) with PASS + FAIL each.
  AC-4: feedback_protocol schema — `comment_type` required,
        `target` kind consistent with `comment_type`.
  AC-6: v3.15 class-based ``SFXReviewer`` remains importable,
        functional, and emits ``DeprecationWarning``.

All cases use pure-Python plan fixtures (no ffmpeg / filesystem).
"""

from __future__ import annotations

import warnings
from typing import Any

import pytest
from pydantic import ValidationError


def _trigger(
    trigger_id: str = "trg_001",
    planned_time_sec: float = 5.0,
    duration_seconds: float = 0.3,
    rationale: str = "emphasis on climax",
    narrative_role: str = "climax",
    sfx_type: str = "whoosh",
    volume_db: float = 0.0,
    span_id: str = "span_01",
    anchor_text: str = "our next big moment arrives",
    keyword_span: tuple[int, int] = (0, 27),
) -> Any:
    from src.shared.schemas.sfx_layout_plan import (
        SfxLayoutTrigger,
        SfxScriptAnchor,
    )

    return SfxLayoutTrigger(
        trigger_id=trigger_id,
        script_anchor=SfxScriptAnchor(span_id=span_id, text=anchor_text),
        keyword_span=list(keyword_span),
        planned_time_sec=planned_time_sec,
        sfx_type=sfx_type,
        rationale=rationale,
        narrative_role=narrative_role,
        volume_db=volume_db,
        duration_seconds=duration_seconds,
    )


def _plan(triggers: list) -> Any:
    from src.shared.schemas.sfx_layout_plan import SfxLayoutPlan

    return SfxLayoutPlan(plan_version=1, triggers=triggers)


# ---------- AC-1 --------------------------------------------------------


class TestAC1ScriptCoverage:
    def test_script_coverage_pass_fail(self) -> None:
        from src.backend.reviewers.sfx_layout_reviewer import SfxLayoutReviewer

        r = SfxLayoutReviewer()
        script_nodes = [
            {"narrative_role": "hook", "time_sec": 1.0},
            {"narrative_role": "climax", "time_sec": 30.0},
            {"narrative_role": "resolution", "time_sec": 60.0},
            {"narrative_role": "cta", "time_sec": 90.0},
        ]
        plan_pass = _plan(
            [
                _trigger("trg_001", planned_time_sec=1.0, narrative_role="hook"),
                _trigger("trg_002", planned_time_sec=30.0, narrative_role="climax"),
                _trigger(
                    "trg_003",
                    planned_time_sec=60.0,
                    narrative_role="resolution",
                ),
            ]
        )
        assert r.check_script_coverage(plan_pass, script_nodes).verdict == "PASS"

        plan_fail = _plan(
            [_trigger("trg_001", planned_time_sec=1.0, narrative_role="hook")]
        )
        assert r.check_script_coverage(plan_fail, script_nodes).verdict == "FAIL"


class TestAC1KeywordAnchor:
    def test_keyword_anchor_overlap(self) -> None:
        from src.backend.reviewers.sfx_layout_reviewer import SfxLayoutReviewer

        r = SfxLayoutReviewer()
        script_text = "the market crashed loudly as investors fled the room"
        plan_pass = _plan(
            [
                _trigger(
                    "trg_001",
                    anchor_text="the market crashed",
                    keyword_span=(0, 18),
                )
            ]
        )
        assert r.check_keyword_anchor(plan_pass, script_text).verdict == "PASS"

        plan_fail = _plan(
            [
                _trigger(
                    "trg_001",
                    anchor_text="completely unrelated here",
                    keyword_span=(0, 18),
                )
            ]
        )
        assert r.check_keyword_anchor(plan_fail, script_text).verdict == "FAIL"


class TestAC1ExplanationCompleteness:
    def test_explanation_completeness(self) -> None:
        from src.backend.reviewers.sfx_layout_reviewer import SfxLayoutReviewer

        r = SfxLayoutReviewer()
        plan_pass = _plan(
            [
                _trigger(
                    "trg_001",
                    rationale="emphasise climax",
                    narrative_role="climax",
                ),
                _trigger(
                    "trg_002",
                    planned_time_sec=30.0,
                    rationale="cta punctuation",
                    narrative_role="cta",
                ),
            ]
        )
        assert r.check_explanation_completeness(plan_pass).verdict == "PASS"

        plan_fail = _plan(
            [
                _trigger(
                    "trg_001",
                    rationale="   ",
                    narrative_role="climax",
                )
            ]
        )
        assert r.check_explanation_completeness(plan_fail).verdict == "FAIL"


class TestAC1Sparsity:
    def test_sparsity(self) -> None:
        from src.backend.reviewers.sfx_layout_reviewer import SfxLayoutReviewer

        r = SfxLayoutReviewer()
        plan_pass = _plan(
            [
                _trigger("trg_001", planned_time_sec=0.0),
                _trigger("trg_002", planned_time_sec=20.0),
                _trigger("trg_003", planned_time_sec=40.0),
            ]
        )
        assert r.check_sparsity(plan_pass).verdict == "PASS"

        plan_fail = _plan(
            [
                _trigger("trg_001", planned_time_sec=0.0),
                _trigger("trg_002", planned_time_sec=5.0),
                _trigger("trg_003", planned_time_sec=15.0),
                _trigger("trg_004", planned_time_sec=25.0),
            ]
        )
        assert r.check_sparsity(plan_fail).verdict == "FAIL"


# ---------- AC-4 --------------------------------------------------------


class TestAC4FeedbackProtocol:
    def test_feedback_protocol_comment_type_required(self) -> None:
        from src.shared.schemas.feedback_protocol import SfxReviewerFeedback

        with pytest.raises(ValidationError):
            SfxReviewerFeedback.model_validate(
                {"target": "trg_001", "action": "add", "payload": {}}
            )
        with pytest.raises(ValidationError):
            SfxReviewerFeedback.model_validate(
                {
                    "comment_type": "bogus_feedback",
                    "target": "trg_001",
                    "action": "add",
                    "payload": {},
                }
            )

    def test_target_type_matches_comment_type(self) -> None:
        from src.shared.schemas.feedback_protocol import SfxReviewerFeedback

        SfxReviewerFeedback(
            comment_type="layout_feedback",
            target="trg_001",
            action="add",
            payload={},
        )
        SfxReviewerFeedback(
            comment_type="mix_feedback",
            target="seg_03",
            action="modify",
            payload={},
        )
        with pytest.raises(ValidationError):
            SfxReviewerFeedback(
                comment_type="layout_feedback",
                target="seg_03",
                action="add",
                payload={},
            )
        with pytest.raises(ValidationError):
            SfxReviewerFeedback(
                comment_type="mix_feedback",
                target="trg_001",
                action="add",
                payload={},
            )


# ---------- AC-6 --------------------------------------------------------


class TestAC6DeprecatedSfxReviewer:
    def test_v315_path_still_passes(self) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            from src.backend.reviewers.sfx_reviewer import (  # noqa: F401
                SFXReviewer,
                sfx_l1_review,
            )

            out = sfx_l1_review({"triggers": []})
            reviewer = SFXReviewer()
            out2 = reviewer.review({"triggers": []})

        assert out.verdict == "PASS"
        assert out2.verdict == "PASS"
        assert any(issubclass(w.category, DeprecationWarning) for w in caught), (
            "deprecated SFXReviewer did not emit DeprecationWarning"
        )
