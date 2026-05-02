"""[SPEC-C-100] SafetyPolicyEngine — 5-level input safety guard (SPEC-4.5 重编号).

Orchestrates: InputClassifier -> PolicyDecision -> ResponseGenerator (template-only)
plus optional event_sink emission of `safety.blocked` with SHA-256 of the raw
input (HARNESS §8/§11: never persist raw user text).
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Callable, Optional, Tuple

from src.backend.agents.safety.input_classifier import InputClassifier
from src.backend.agents.safety.policy_decision import PolicyDecision
from src.backend.agents.safety.response_generator import ResponseGenerator


EventSink = Callable[[dict[str, Any]], None]


class SafetyPolicyEngine:
    """Entry point for input safety classification + templated response.

    - refuse/restrict/clarify/transfer_human paths never touch the LLM client
      (AC-2); the ``llm_client`` argument is accepted for interface parity but
      is never consumed here.
    - non-``allow`` decisions emit a ``safety.blocked`` event through
      ``event_sink`` with a SHA-256 hash of the raw input only (AC-4).
    """

    def __init__(
        self,
        *,
        rules_path: str | Path,
        templates_path: str | Path,
        event_sink: Optional[EventSink] = None,
        llm_client: Any = None,
    ) -> None:
        self._classifier = InputClassifier(rules_path)
        self._response = ResponseGenerator(templates_path)
        self._event_sink = event_sink
        self._llm_client = llm_client  # retained for interface parity only

    def evaluate(self, user_input: str) -> Tuple[PolicyDecision, str]:
        decision = self._classifier.classify(user_input)
        response = self._response.render(decision.decision)
        if decision.decision != "allow":
            self._emit_blocked(user_input, decision)
        return decision, response

    def evaluate_as_dict(self, user_input: str) -> dict[str, Any]:
        decision, response_text = self.evaluate(user_input)
        return {
            "action": decision.decision,
            "decision": {
                "action": decision.decision,
                "matched_rule_id": decision.matched_rule_id,
            },
            "reply_to_user": response_text,
            "response_text": response_text,
        }

    def _emit_blocked(self, user_input: str, decision: PolicyDecision) -> None:
        if self._event_sink is None:
            return
        digest = hashlib.sha256(user_input.encode("utf-8")).hexdigest()
        self._event_sink(
            {
                "event_type": "safety.blocked",
                "user_input_hash": digest,
                "decision": decision.decision,
                "matched_rule_id": decision.matched_rule_id,
            }
        )
