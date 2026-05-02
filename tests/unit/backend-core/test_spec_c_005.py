"""Tests for [SPEC-C-005] Version Management & Review Supersede.

Real tests in test_version_manager.py. Re-exports for canonical discovery via subclassing.
"""

from __future__ import annotations

from importlib.machinery import SourceFileLoader
from pathlib import Path

_dir = Path(__file__).parent
_ = SourceFileLoader(
    "test_version_manager", str(_dir / "test_version_manager.py")
).load_module()


class TestAC1GenerateArtifactIncrementsVersion(
    _.TestAC1GenerateArtifactIncrementsVersion
):
    pass


class TestAC2UserRevisionIncrementsVersion(_.TestAC2UserRevisionIncrementsVersion):
    pass


class TestAC3AutoCreateReviewForNewVersion(_.TestAC3AutoCreateReviewForNewVersion):
    pass


class TestAC4OldReviewsSuperseded(_.TestAC4OldReviewsSuperseded):
    pass


class TestAC5NoDuplicatePendingReviews(_.TestAC5NoDuplicatePendingReviews):
    pass


class TestAC6SupersededNotDispatched(_.TestAC6SupersededNotDispatched):
    pass
