"""[SPEC-D-002] Gate-P0: validates P0 outputs before advancing to P1.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.0.3
"""

from __future__ import annotations

from typing import Any

from src.backend.gates.base_gate import BaseGate


class GateP0(BaseGate):
    """Check: requirements present, reviewer PASS."""

    def __init__(self, requirements: dict[str, Any] | None = None) -> None:
        super().__init__()
        self.requirements: dict[str, Any] = requirements or {}
        self.register_checks(["check_requirements_exist", "check_completeness_reviewer"])

    def check_requirements_exist(self) -> tuple[bool, str]:
        if not self.requirements or not self.requirements.get("project_id"):
            return False, "requirements.json missing or empty"
        return True, "requirements.json exists"

    def check_completeness_reviewer(self) -> tuple[bool, str]:
        from src.backend.agents.completeness_reviewer import CompletenessReviewer

        reviewer = CompletenessReviewer()
        verdict = reviewer.review(self.requirements)
        if verdict["verdict"] == "PASS":
            return True, "CompletenessReviewer PASS"
        return False, f"CompletenessReviewer FAIL: {verdict['blocking_issues']}"

    @staticmethod
    def check(requirements: dict[str, Any]) -> dict[str, Any]:
        """Static convenience — for direct test calls and backward compat."""
        gate = GateP0(requirements)
        result = gate.run()
        return {
            "passed": result.passed,
            "failed_checks": result.failed_checks,
            "passed_checks": result.passed_checks,
        }
