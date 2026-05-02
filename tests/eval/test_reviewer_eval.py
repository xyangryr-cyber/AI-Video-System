"""Eval set for Reviewer agent accuracy."""

import pytest


class TestReviewerAccuracy:
    """Reviewer must detect issues with >= 85% recall on eval set."""

    def test_eval_set_baseline(self):
        pytest.skip("NOT IMPLEMENTED -- waiting for SPEC-D-010 + eval data")
