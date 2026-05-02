"""Tests for [SPEC-C-010] Reviewer Agent & Dual-Layer Architecture (L1 + L2).

Authority: docs/specs/SPEC-C-backend-core.md SPEC-5.2 / SPEC-5.3.
Task card: tasks/SPEC-C/C-010-reviewer-dual-layer.md.

Acceptance mapping
------------------
AC-1  ``verdict`` only accepts ``PASS`` or ``FAIL``, no intermediate states.
      -> :class:`TestAC1VerdictOnlyPassOrFail`
AC-2  ``blocking_issues`` non-empty implies ``verdict=FAIL``; empty implies PASS.
      -> :class:`TestAC2BlockingIssuesImpliesFail`
AC-3  L1 failure prevents L2 invocation (token consumption = 0).
      -> :class:`TestAC3L1FailSkipsL2`
AC-4  6 pure-L1 Reviewers (AudioQuality, AVSync, SFX, Storyboard, Visual, Final)
      consume 0 tokens on any call.
      -> :class:`TestAC4PureL1ZeroTokens`
AC-5  6 hybrid L1+L2 Reviewers (Completeness, Structure, Style, FactChecker,
      MusicFit, BRollFit) trigger L2 only after L1 passes.
      -> :class:`TestAC5HybridL2AfterL1Pass`
AC-6  All 12 Reviewer types are registered and discoverable.
      -> :class:`TestAC6TwelveReviewersRegistered`
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from src.backend.agents import reviewer_agent


PURE_L1_REVIEWERS = (
    "AudioQualityReviewer",
    "AVSyncReviewer",
    "SFXReviewer",
    "StoryboardReviewer",
    "VisualReviewer",
    "FinalReviewer",
)

HYBRID_REVIEWERS = (
    "CompletenessReviewer",
    "StructureReviewer",
    "StyleReviewer",
    "FactCheckerReviewer",
    "MusicFitReviewer",
    "BRollFitReviewer",
)

ALL_REVIEWERS = PURE_L1_REVIEWERS + HYBRID_REVIEWERS


def _passing_l2(artifact: Any) -> reviewer_agent.ReviewerOutput:
    return reviewer_agent.ReviewerOutput(verdict="PASS", notes=[], blocking_issues=[])


# -- AC-1 ----------------------------------------------------------------


class TestAC1VerdictOnlyPassOrFail:
    """AC-1: ``verdict`` only accepts ``PASS`` or ``FAIL``, no intermediate states"""

    def test_verdict_only_pass_or_fail(self):
        ok = reviewer_agent.ReviewerOutput(verdict="PASS", notes=[], blocking_issues=[])
        assert ok.verdict == "PASS"
        bad = reviewer_agent.ReviewerOutput(
            verdict="FAIL", notes=[], blocking_issues=["x"]
        )
        assert bad.verdict == "FAIL"

        for invalid in ("WARN", "warning", "pass", "fail", "UNKNOWN", "", "NEEDS_FIX"):
            with pytest.raises(ValidationError):
                reviewer_agent.ReviewerOutput(
                    verdict=invalid,  # type: ignore[arg-type]
                    notes=[],
                    blocking_issues=[],
                )


# -- AC-2 ----------------------------------------------------------------


class TestAC2BlockingIssuesImpliesFail:
    """AC-2: ``blocking_issues`` non-empty implies ``verdict=FAIL``"""

    def test_blocking_issues_implies_fail(self):
        with pytest.raises(ValidationError):
            reviewer_agent.ReviewerOutput(
                verdict="PASS",
                notes=[],
                blocking_issues=["missing output_schema"],
            )
        obj = reviewer_agent.ReviewerOutput(
            verdict="FAIL",
            notes=[],
            blocking_issues=["missing output_schema"],
        )
        assert obj.blocking_issues == ["missing output_schema"]

    def test_empty_blocking_implies_pass(self):
        with pytest.raises(ValidationError):
            reviewer_agent.ReviewerOutput(
                verdict="FAIL",
                notes=["style nit"],
                blocking_issues=[],
            )
        obj = reviewer_agent.ReviewerOutput(
            verdict="PASS",
            notes=["style nit"],
            blocking_issues=[],
        )
        assert obj.verdict == "PASS"


# -- AC-3 ----------------------------------------------------------------


class TestAC3L1FailSkipsL2:
    """AC-3: L1 failure prevents L2 invocation (token consumption = 0)"""

    def test_l1_fail_skips_l2(self):
        calls: dict[str, int] = {"l2": 0}

        def failing_l1(artifact: Any) -> reviewer_agent.ReviewerOutput:
            return reviewer_agent.ReviewerOutput(
                verdict="FAIL",
                notes=[],
                blocking_issues=["missing required field"],
            )

        def tracking_l2(artifact: Any) -> reviewer_agent.ReviewerOutput:
            calls["l2"] += 1
            return reviewer_agent.ReviewerOutput(
                verdict="PASS", notes=[], blocking_issues=[]
            )

        reviewer = reviewer_agent.HybridReviewer(
            name="TestHybridReviewer", l1=failing_l1, l2=tracking_l2
        )
        result = reviewer.review({"any": "artifact"})

        assert result.verdict == "FAIL"
        assert result.blocking_issues == ["missing required field"]
        assert calls["l2"] == 0
        assert result.tokens_used == 0


# -- AC-4 ----------------------------------------------------------------


class TestAC4PureL1ZeroTokens:
    """AC-4: 6 pure-L1 Reviewers consume 0 tokens on any call"""

    @pytest.mark.parametrize("name", PURE_L1_REVIEWERS)
    def test_pure_l1_zero_tokens(self, name):
        reviewer = reviewer_agent.get_reviewer(name)
        assert isinstance(reviewer, reviewer_agent.PureL1Reviewer)
        result = reviewer.review({"artifact": "whatever"})
        assert result.tokens_used == 0
        assert result.verdict in ("PASS", "FAIL")


# -- AC-5 ----------------------------------------------------------------


class TestAC5HybridL2AfterL1Pass:
    """AC-5: 6 hybrid L1+L2 Reviewers trigger L2 only after L1 passes"""

    @pytest.mark.parametrize("name", HYBRID_REVIEWERS)
    def test_hybrid_l2_after_l1_pass(self, name):
        calls: dict[str, int] = {"l2": 0}

        def tracking_l2(artifact: Any) -> reviewer_agent.ReviewerOutput:
            calls["l2"] += 1
            return reviewer_agent.ReviewerOutput(
                verdict="PASS", notes=["l2 ok"], blocking_issues=[]
            )

        reviewer = reviewer_agent.get_reviewer(name, l2=tracking_l2)
        assert isinstance(reviewer, reviewer_agent.HybridReviewer)

        result = reviewer.review({"valid": True})
        assert calls["l2"] == 1
        assert result.verdict == "PASS"

        # When L1 fails, L2 MUST NOT be invoked.
        calls["l2"] = 0
        failing = reviewer_agent.HybridReviewer(
            name=name,
            l1=lambda _a: reviewer_agent.ReviewerOutput(
                verdict="FAIL",
                notes=[],
                blocking_issues=["l1 blocker"],
            ),
            l2=tracking_l2,
        )
        out = failing.review({"valid": True})
        assert out.verdict == "FAIL"
        assert calls["l2"] == 0


# -- AC-6 ----------------------------------------------------------------


class TestAC6TwelveReviewersRegistered:
    """AC-6: All 12 Reviewer types are registered and discoverable"""

    def test_twelve_reviewers_registered(self):
        names = set(reviewer_agent.list_reviewers())
        assert set(ALL_REVIEWERS) <= names, f"missing: {set(ALL_REVIEWERS) - names}"
        assert len(names & set(ALL_REVIEWERS)) == 12

        for n in PURE_L1_REVIEWERS:
            r = reviewer_agent.get_reviewer(n)
            assert isinstance(r, reviewer_agent.PureL1Reviewer)
        for n in HYBRID_REVIEWERS:
            r = reviewer_agent.get_reviewer(n, l2=_passing_l2)
            assert isinstance(r, reviewer_agent.HybridReviewer)
