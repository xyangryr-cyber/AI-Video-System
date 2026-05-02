"""[SPEC-D-010] L1Reviewer -- 0-token programmatic review framework.

Authority: docs/specs/SPEC-D-pipeline-phases.md "L1 Reviewer Framework"

Placed outside reviewers/ package to avoid circular import.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.backend.agents.base_reviewer import BaseReviewer


class L1Reviewer(BaseReviewer):
    """Base class for L1 programmatic reviewers.

    - Check functions registered via register_checks().
    - Each check returns (pass: bool, note: str).
    - 0 LLM tokens (enforced).
    - skip_l2_on_fail flag when L1 fails.
    """

    def __init__(self) -> None:
        self._checks: list[str] = []
        self._check_fn: dict[str, Callable[..., Any]] = {}

    def register_checks(self, check_names: list[str]) -> None:
        self._checks = list(check_names)
        for name in check_names:
            self._check_fn[name] = getattr(self, name)

    def review(self, artifact: Any) -> dict[str, Any]:
        notes: list[str] = []
        blocking: list[str] = []
        any_fail = False

        for name in self._checks:
            fn = self._check_fn[name]
            passed, detail = fn(artifact)
            if passed:
                notes.append(detail)
            else:
                any_fail = True
                blocking.append(f"{name}: {detail}")

        return {
            "verdict": "FAIL" if any_fail else "PASS",
            "notes": notes,
            "blocking_issues": blocking,
            "token_count": 0,
            "skip_l2_on_fail": any_fail,
        }
