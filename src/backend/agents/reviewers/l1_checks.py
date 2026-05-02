"""[SPEC-C-010] L1 (programmatic) checks for all 12 Reviewers.

Authority: docs/specs/SPEC-C-backend-core.md SPEC-5.3.

Each function takes an artifact (``Any`` -- usually a dict) and returns a
:class:`~src.backend.agents.reviewer_agent.ReviewerOutput`. Functions here
MUST NOT call any LLM; they are the "0-token" layer that gates L2.

The checks below are minimal-viable placeholders that satisfy the
SPEC-5.2 invariants (verdict/blocking_issues consistency) and let the
dual-layer architecture be exercised end-to-end. Per-reviewer rule sets
(e.g. MusicFit's v3.15 4 items + C-AUDP7A-3 extensions) are layered on
top of this scaffold in later task cards (SPEC-C-018, SPEC-C-020 etc.).
"""

from __future__ import annotations

from typing import Any, Mapping

from src.backend.agents.reviewer_agent import ReviewerOutput


def _is_mapping(artifact: Any) -> bool:
    return isinstance(artifact, Mapping)


def _pass(note: str | None = None) -> ReviewerOutput:
    return ReviewerOutput(
        verdict="PASS",
        notes=[note] if note else [],
        blocking_issues=[],
    )


def _fail(reason: str) -> ReviewerOutput:
    return ReviewerOutput(
        verdict="FAIL",
        notes=[],
        blocking_issues=[reason],
    )


def _basic_shape(artifact: Any, reviewer: str) -> ReviewerOutput:
    """Shared L1 shape check: artifact must be a non-None mapping-like."""
    if artifact is None:
        return _fail(f"{reviewer}: artifact is None")
    if not _is_mapping(artifact):
        return _fail(
            f"{reviewer}: artifact must be a mapping, got {type(artifact).__name__}"
        )
    return _pass()


# -- Pure-L1 reviewers ---------------------------------------------------


def audio_quality_l1(artifact: Any) -> ReviewerOutput:
    return _basic_shape(artifact, "AudioQualityReviewer")


def av_sync_l1(artifact: Any) -> ReviewerOutput:
    return _basic_shape(artifact, "AVSyncReviewer")


def sfx_l1(artifact: Any) -> ReviewerOutput:
    return _basic_shape(artifact, "SFXReviewer")


def storyboard_l1(artifact: Any) -> ReviewerOutput:
    return _basic_shape(artifact, "StoryboardReviewer")


def visual_l1(artifact: Any) -> ReviewerOutput:
    return _basic_shape(artifact, "VisualReviewer")


def final_l1(artifact: Any) -> ReviewerOutput:
    return _basic_shape(artifact, "FinalReviewer")


# -- Hybrid reviewers (L1 half) ------------------------------------------


def completeness_l1(artifact: Any) -> ReviewerOutput:
    return _basic_shape(artifact, "CompletenessReviewer")


def structure_l1(artifact: Any) -> ReviewerOutput:
    return _basic_shape(artifact, "StructureReviewer")


def style_l1(artifact: Any) -> ReviewerOutput:
    return _basic_shape(artifact, "StyleReviewer")


def fact_checker_l1(artifact: Any) -> ReviewerOutput:
    return _basic_shape(artifact, "FactCheckerReviewer")


def music_fit_l1(artifact: Any) -> ReviewerOutput:
    return _basic_shape(artifact, "MusicFitReviewer")


def broll_fit_l1(artifact: Any) -> ReviewerOutput:
    return _basic_shape(artifact, "BRollFitReviewer")


__all__ = [
    "audio_quality_l1",
    "av_sync_l1",
    "sfx_l1",
    "storyboard_l1",
    "visual_l1",
    "final_l1",
    "completeness_l1",
    "structure_l1",
    "style_l1",
    "fact_checker_l1",
    "music_fit_l1",
    "broll_fit_l1",
]
