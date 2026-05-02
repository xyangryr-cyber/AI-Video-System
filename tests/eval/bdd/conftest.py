"""Fixtures for eval-bucket BDD scenarios.

Action-label assertions use a deterministic alias matcher rather than an LLM
judge: the Then-criteria are exact-equality + a tiny alias map, and an LLM
judge for that adds API cost, latency, and flakiness without any benefit
("clarify == clarify" needs no semantic model). Reserve LLM-judge fixtures
for scenarios that genuinely need free-text semantic evaluation.
"""

from __future__ import annotations

import os
from typing import Callable

import pytest


# Map expected canonical action -> accepted equivalents from IntentRouter.
# Extend here when SPEC adds a new alias; do not scatter alias logic across
# step defs.
ACTION_ALIASES: dict[str, frozenset[str]] = {
    "revise": frozenset({"revise", "局部修改"}),
    "regenerate": frozenset(
        {"regenerate", "regenerate_section", "整体重做"}
    ),
    "inject_subtask": frozenset({"inject_subtask", "insert_section"}),
    # SPEC-4.6 forbids the router from emitting a real advance action; the
    # canonical advance signal is action="clarify" + highlight_confirm_button.
    # We accept "clarify" here so the alias matcher can recognise the
    # advance-clarify pair, but the BDD step (assert_action_request_advance)
    # additionally requires highlight_confirm_button=True so a plain clarify
    # (without advance hint) still fails the assertion.
    "request_advance": frozenset(
        {"request_advance", "confirm_next", "advance", "clarify"}
    ),
    "clarify": frozenset({"clarify"}),
    "skip_phase": frozenset({"skip_phase"}),
}


def _matches_action(actual: str, expected: str) -> bool:
    return actual in ACTION_ALIASES.get(expected, frozenset({expected}))


@pytest.fixture
def scenario_state():
    """Mirror the integration bucket -- mutable per-scenario dict."""
    return {}


@pytest.fixture(scope="session")
def require_eval_mode():
    """Skip all scenarios unless AVS_EVAL_MODE=1.

    Kept after dropping the LLM judge for these specific scenarios so the
    eval bucket as a whole still gates behind the env flag (other eval
    scenarios may still call real LLMs).
    """
    if os.environ.get("AVS_EVAL_MODE") != "1":
        pytest.skip("eval bucket off (set AVS_EVAL_MODE=1 to enable)")


@pytest.fixture
def action_matcher(require_eval_mode) -> Callable[[str, str], bool]:
    """Return ``(actual, expected) -> bool`` checking against ACTION_ALIASES."""
    return _matches_action
