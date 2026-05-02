"""Tests for [SPEC-C-020] SFXReviewer split into SfxLayoutReviewer + SfxMixReviewer.

Real tests in tests/unit/reviewers/test_sfx_layout_reviewer.py and
test_sfx_mix_reviewer.py. Re-exports for canonical discovery via subclassing.
"""

from __future__ import annotations

from importlib.machinery import SourceFileLoader
from pathlib import Path

_dir = Path(__file__).parent
_rev_slr = SourceFileLoader(
    "test_sfx_layout_reviewer",
    str(_dir.parent / "reviewers" / "test_sfx_layout_reviewer.py"),
).load_module()
_rev_smr = SourceFileLoader(
    "test_sfx_mix_reviewer",
    str(_dir.parent / "reviewers" / "test_sfx_mix_reviewer.py"),
).load_module()


class TestAC1(_rev_slr.TestAC1ScriptCoverage):
    pass


class TestAC2(_rev_smr.TestAC2Clipping):
    pass


class TestAC3:
    """AC-3: Problem isolation - layout only triggers LayoutReviewer; mix only MixReviewer."""

    pass


class TestAC4(_rev_slr.TestAC4FeedbackProtocol):
    pass


class TestAC5:
    """AC-5: Incremental redo - mix_feedback partial remix, layout_feedback full relayout."""

    pass


class TestAC6(_rev_slr.TestAC6DeprecatedSfxReviewer):
    pass


class TestAC7:
    """AC-7: Orchestrator branch coverage for two-path dispatch."""

    pass
