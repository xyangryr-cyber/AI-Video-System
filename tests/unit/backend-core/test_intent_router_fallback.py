"""Tests for [SPEC-C-007] IntentRouter Error Handling, Clarify Flow & confirm_next Bypass.

AC mapping:
  AC-1  test_non_json_returns_clarify
  AC-2  test_timeout_returns_clarify
  AC-3  test_fallback_logs_event
  AC-4  test_two_clarifies_show_buttons
  AC-5  test_success_resets_clarify_count
  AC-6  test_advance_text_not_routed
"""

from __future__ import annotations

import time

from src.backend.agents.intent_router import IntentRouter

_ROUTER = IntentRouter()


class TestAC1NonJsonReturnsClarify:
    """AC-1: LLM returning non-JSON causes Router to return `clarify` action, not HTTP 500"""

    def test_non_json_returns_clarify(self):
        result = _ROUTER.route(
            lambda: "this is not json", clarify_count=0, timeout_seconds=3.0
        )
        assert result["action"] == "clarify"


class TestAC2TimeoutReturnsClarify:
    """AC-2: LLM exceeding 3s timeout causes Router to return `clarify` action"""

    def test_timeout_returns_clarify(self):
        def slow_llm() -> str:
            time.sleep(10)
            return '{"action": "revise"}'

        result = _ROUTER.route(slow_llm, clarify_count=0, timeout_seconds=0.05)
        assert result["action"] == "clarify"


class TestAC3FallbackLogsEvent:
    """AC-3: All fallback scenarios produce a `router_fallback` log entry"""

    def test_fallback_logs_event(self):
        result = _ROUTER.route(lambda: "not json", clarify_count=0, timeout_seconds=3.0)
        events = result.get("events", [])
        assert any(e.get("type") == "router_fallback" for e in events)


class TestAC4TwoClarifiesShowButtons:
    """AC-4: After 2 consecutive clarify responses, output includes <=4 candidate action buttons"""

    def test_two_clarifies_show_buttons(self):
        # clarify_count=1: 1 prior clarify; this parse-failure is the 2nd -> show buttons
        result = _ROUTER.route(lambda: "bad json", clarify_count=1, timeout_seconds=3.0)
        assert result["action"] == "clarify"
        candidates = result.get("candidate_actions")
        assert candidates is not None, (
            "candidate_actions must be populated after 2 clarifies"
        )
        assert 1 <= len(candidates) <= 4


class TestAC5SuccessResetsClarifyCount:
    """AC-5: Successful operation resets clarify counter to 0"""

    def test_success_resets_clarify_count(self):
        result = _ROUTER.route(
            lambda: '{"action": "revise", "params": {}}',
            clarify_count=2,
            timeout_seconds=3.0,
        )
        assert result["action"] == "revise"
        assert result["clarify_count"] == 0


class TestAC6AdvanceTextNotRouted:
    """AC-6: `confirm_next` is never routed through the Router (hard front-end button)"""

    def test_advance_text_not_routed(self):
        # Even if LLM returns confirm_next, Router must not pass it through
        result = _ROUTER.route(
            lambda: '{"action": "confirm_next", "params": {}}',
            clarify_count=0,
            timeout_seconds=3.0,
        )
        assert result["action"] == "clarify"
