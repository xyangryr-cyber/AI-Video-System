"""[SPEC-G-013] Keyword-rule unit tests for IntentRouter.classify().

Authority: docs/specs/SPEC-C-backend-core.md SPEC-4.1, SPEC-4.4, SPEC-4.6.

Scope per task card:
- regenerate intent  -> action="regenerate_section" + scope=full + generate_artifact ledger
- advance intent     -> action="clarify" + highlight_confirm_button=True
                        (SPEC-4.6 forbids a real advance action; UI signal only)
- unknown utterance  -> action="clarify" with NO advance hint
- existing revise rule unchanged (regression guard)
"""

from __future__ import annotations

from src.backend.agents.intent_router import IntentRouter


class TestRegenerateIntent:
    def test_classify_recognizes_regenerate_intent(self) -> None:
        result = IntentRouter().classify("这版大纲不对，整体重做")
        assert result["action"] == "regenerate_section"
        assert result["params"]["scope"] == "full"
        assert any(
            t.get("type") == "generate_artifact"
            for t in result.get("task_ledger", [])
        )


class TestAdvanceIntentReturnsClarifyWithHint:
    def test_classify_recognizes_advance_intent_returns_clarify_with_hint(self) -> None:
        result = IntentRouter().classify("好了，下一步")
        assert result["action"] == "clarify"  # SPEC-4.6: no real advance action
        assert result["highlight_confirm_button"] is True
        assert result["gate_satisfied"] is False
        assert "确认" in result["reply_to_user"]


class TestClarifyFallbackForUnknown:
    def test_classify_falls_back_to_clarify_for_unknown(self) -> None:
        result = IntentRouter().classify("嗯……感觉怪怪的")
        assert result["action"] == "clarify"
        assert result.get("highlight_confirm_button") is not True


class TestRegressionReviseRuleUnchanged:
    def test_classify_revise_unchanged_by_new_rules(self) -> None:
        result = IntentRouter().classify("把第二段改得更口语化")
        assert result["action"] == "revise"
