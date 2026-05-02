"""[SPEC-C-100] PolicyDecision — 5-level safety decision dataclass."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

DecisionLevel = Literal["allow", "clarify", "restrict", "refuse", "transfer_human"]

DECISION_LEVELS: tuple[DecisionLevel, ...] = (
    "allow",
    "clarify",
    "restrict",
    "refuse",
    "transfer_human",
)


@dataclass(frozen=True)
class PolicyDecision:
    decision: DecisionLevel
    matched_rule_id: str | None
    reason: str
