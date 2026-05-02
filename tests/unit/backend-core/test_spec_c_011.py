"""Tests for [SPEC-C-011] LiteLLM + Instructor Integration & Model Routing Config.

Real tests in test_llm_service.py. Re-exports for canonical discovery via subclassing.
"""

from __future__ import annotations

from importlib.machinery import SourceFileLoader
from pathlib import Path

_dir = Path(__file__).parent
_ = SourceFileLoader(
    "test_llm_service", str(_dir / "test_llm_service.py")
).load_module()


class TestAC1NoDirectOpenaiCalls(_.TestAC1NoDirectOpenAICalls):
    pass


class TestAC2InstructorRetriesOnFormatError(_.TestAC2RetryOnFormatError):
    pass


class TestAC3ModelConfigHasFiveKeys(_.TestAC3ModelConfigFiveKeys):
    pass


class TestAC4ConfigChangeAppliesNewModel(_.TestAC4ConfigChangeAppliesNewModel):
    pass


class TestAC5AllCallsThroughLlmService(_.TestAC5SingleEntryPointUsesLitellm):
    pass
