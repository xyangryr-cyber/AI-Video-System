"""Eval set for IntentRouter agent accuracy."""

import pytest


class TestRouterAccuracy:
    """Router must classify intents with >= 90% accuracy on eval set."""

    def test_eval_set_baseline(self):
        pytest.skip("NOT IMPLEMENTED -- waiting for SPEC-C-006 + eval data")
