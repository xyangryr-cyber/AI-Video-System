"""[SPEC-C-100] InputClassifier — regex-rule-based 5-level classifier with hot reload."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from src.backend.agents.safety.policy_decision import (
    DECISION_LEVELS,
    DecisionLevel,
    PolicyDecision,
)


@dataclass(frozen=True)
class _Rule:
    id: str
    pattern: re.Pattern[str]
    decision: DecisionLevel


class InputClassifier:
    """Stateless-per-call classifier; file-backed with mtime-hot-reload."""

    def __init__(self, rules_path: str | Path) -> None:
        self._path = Path(rules_path)
        self._mtime: float | None = None
        self._rules: list[_Rule] = []
        self._default: DecisionLevel = "allow"
        self._load()

    def _load(self) -> None:
        raw = yaml.safe_load(self._path.read_text(encoding="utf-8")) or {}
        default = raw.get("default_decision", "allow")
        if default not in DECISION_LEVELS:
            raise ValueError(f"invalid default_decision: {default!r}")
        rules: list[_Rule] = []
        for r in raw.get("rules") or []:
            decision = r["decision"]
            if decision not in DECISION_LEVELS:
                raise ValueError(
                    f"invalid decision on rule {r.get('id')!r}: {decision!r}"
                )
            rules.append(
                _Rule(
                    id=str(r["id"]),
                    pattern=re.compile(r["pattern"]),
                    decision=decision,
                )
            )
        self._rules = rules
        self._default = default
        self._mtime = self._path.stat().st_mtime

    def _maybe_reload(self) -> None:
        try:
            cur = self._path.stat().st_mtime
        except FileNotFoundError:
            return
        if cur != self._mtime:
            self._load()

    def classify(self, user_input: str) -> PolicyDecision:
        self._maybe_reload()
        for r in self._rules:
            if r.pattern.search(user_input):
                return PolicyDecision(
                    decision=r.decision,
                    matched_rule_id=r.id,
                    reason=f"matched_rule:{r.id}",
                )
        return PolicyDecision(
            decision=self._default,
            matched_rule_id=None,
            reason="no_rule_matched",
        )
