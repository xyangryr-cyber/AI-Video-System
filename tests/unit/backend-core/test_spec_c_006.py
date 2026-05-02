"""Tests for [SPEC-C-006] IntentRouter Core (Stateless Design + Context Injection + Model Config).

Real tests in test_intent_router.py. Re-exports for canonical discovery via subclassing.
"""

from __future__ import annotations

from importlib.machinery import SourceFileLoader
from pathlib import Path

_dir = Path(__file__).parent
_ = SourceFileLoader(
    "test_intent_router", str(_dir / "test_intent_router.py")
).load_module()


class TestAC1RouterNoInstanceState(_.TestAC1RouterNoInstanceState):
    pass


class TestAC2RouterUsableWithoutWarmup(_.TestAC2RouterUsableWithoutWarmup):
    pass


class TestAC3ArtifactSnapshotTruncation(_.TestAC3ArtifactSnapshotTruncation):
    pass


class TestAC4ConversationLatestSix(_.TestAC4ConversationLatestSix):
    pass


class TestAC5ConfirmNextNotInActions(_.TestAC5ConfirmNextNotInActions):
    pass


class TestAC6ModelFromConfigNotHardcoded(_.TestAC6ModelFromConfigNotHardcoded):
    pass


class TestAC7ConfigChangeAppliesNewModel(_.TestAC7ConfigChangeAppliesNewModel):
    pass
