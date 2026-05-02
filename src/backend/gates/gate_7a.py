"""[SPEC-D-021] Gate-7A: material readiness gate before P8 + FSM re-entry edges."""

from __future__ import annotations

from typing import Any


class Gate7A:
    """Gate-7A: validates material readiness before advancing to P8.
    Allows re-entry from P8 back to phase_7a."""

    @staticmethod
    def check(
        *,
        hard_materials_verified: bool = False,
        soft_materials_ready: bool = False,
        advanced_to_p8: bool = False,
    ) -> dict[str, Any]:
        failed: list[str] = []
        passed: list[str] = []

        if not hard_materials_verified:
            failed.append("hard materials not verified")
        else:
            passed.append("hard materials verified")

        if soft_materials_ready:
            passed.append("soft materials ready")

        if advanced_to_p8:
            passed.append("already advanced to P8")

        return {
            "passed": len(failed) == 0,
            "failed_checks": failed,
            "passed_checks": passed,
        }

    @staticmethod
    def can_reenter_7a(*, from_phase: int) -> bool:
        return from_phase >= 7
