"""[SPEC-C-020] Deprecated v3.15 SFXReviewer single-layer shim.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-5.

v3.17 split the single-layer ``SFXReviewer`` into
:class:`~src.backend.reviewers.sfx_layout_reviewer.SfxLayoutReviewer` +
:class:`~src.backend.reviewers.sfx_mix_reviewer.SfxMixReviewer`, with
:class:`~src.backend.reviewers.sfx_reviewer_orchestrator.SfxReviewerOrchestrator`
as the unified entry point. This module keeps the v3.15 class-based
``SFXReviewer`` surface importable for **two release cycles** (AC-6) so
downstream callers can migrate incrementally. Every usage emits a
``DeprecationWarning``; the underlying PASS/FAIL contract is the same
``ReviewerOutput`` shape SPEC-C-010 ``sfx_l1`` already produces.
"""

from __future__ import annotations

import warnings
from typing import Any

from src.backend.agents.reviewer_agent import ReviewerOutput
from src.backend.agents.reviewers.l1_checks import sfx_l1

_DEPRECATION_MSG = (
    "SFXReviewer (v3.15 single-layer) is deprecated. Use "
    "SfxLayoutReviewer + SfxMixReviewer via SfxReviewerOrchestrator "
    "(SPEC-C-020 / C-AUDP7A-5). Scheduled for removal after two "
    "release cycles."
)


def sfx_l1_review(artifact: Any) -> ReviewerOutput:
    """Deprecated function-style entry point — delegates to SPEC-C-010 sfx_l1."""
    warnings.warn(_DEPRECATION_MSG, DeprecationWarning, stacklevel=2)
    return sfx_l1(artifact)


class SFXReviewer:
    """Deprecated class-style entry point retained for two release cycles."""

    def __init__(self) -> None:
        warnings.warn(_DEPRECATION_MSG, DeprecationWarning, stacklevel=2)

    def review(self, artifact: Any) -> ReviewerOutput:
        return sfx_l1(artifact)


__all__ = ["SFXReviewer", "sfx_l1_review"]
