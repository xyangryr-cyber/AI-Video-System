"""[SPEC-D-017] FailureRecovery -- per-phase retry limits and recovery actions.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.12
"""

from __future__ import annotations

from typing import Any

_PHASE_RETRY_LIMITS: dict[int, int] = {
    0: 5,
    1: 5,
    2: 5,
    3: 5,
    4: 3,
    5: 3,
    6: 3,
    7: 3,
    8: 3,
    9: 3,
    10: 3,
    11: 3,
}

_PROVIDER_FALLBACK_PHASES = {4, 5, 6, 8, 9}


class FailureRecovery:
    """Per-phase retry limits and failure recovery actions."""

    @staticmethod
    def max_retries(*, phase: int) -> int:
        return _PHASE_RETRY_LIMITS.get(phase, 5)

    @staticmethod
    def should_retry(*, phase: int, attempt: int, max_retries: int | None = None) -> bool:
        limit = max_retries if max_retries is not None else _PHASE_RETRY_LIMITS.get(phase, 5)
        return attempt < limit

    @staticmethod
    def handle_p0_short_description(*, description: str) -> dict[str, Any]:
        if len(description) < 300:
            return {"action": "prompt_user", "reason": "description < 300 chars"}
        return {"action": "proceed"}

    @staticmethod
    def handle_phase_failure(*, phase: int, consecutive_fails: int) -> dict[str, Any]:
        if phase == 3 and consecutive_fails >= 5:
            return {"action": "freeze", "detail": "freeze current + manual edit mode"}
        if consecutive_fails >= _PHASE_RETRY_LIMITS.get(phase, 5):
            return {
                "action": "suggest_return",
                "detail": f"suggest return to phase {max(0, phase - 1)}",
            }
        return {"action": "retry"}

    @staticmethod
    def has_provider_fallback(*, phase: int) -> bool:
        return phase in _PROVIDER_FALLBACK_PHASES
