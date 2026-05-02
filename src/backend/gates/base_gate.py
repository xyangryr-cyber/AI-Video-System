"""[SPEC-D-012] BaseGate -- unified gate checking framework.

Authority: docs/specs/SPEC-D-pipeline-phases.md "Unified Gate Checking Framework"
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from src.shared.constants.error_codes import ErrorCode


@dataclass
class GateResult:
    passed: bool
    failed_checks: list[str] = field(default_factory=list)
    passed_checks: list[str] = field(default_factory=list)


class BaseGate:
    """Base class for all phase gates.

    Check functions registered via register_checks(). Each returns (pass: bool, detail: str).
    Provides skip mode, async completion check, artifact status validation, EVID_2001 error.
    """

    def __init__(self) -> None:
        self._checks: list[str] = []
        self._check_fn: dict[str, Callable[..., Any]] = {}

    def register_checks(self, check_names: list[str]) -> None:
        self._checks = list(check_names)
        for name in check_names:
            self._check_fn[name] = getattr(self, name)

    def run(self) -> GateResult:
        failed: list[str] = []
        passed: list[str] = []
        for name in self._checks:
            fn = self._check_fn[name]
            ok, detail = fn()
            if ok:
                passed.append(detail)
            else:
                failed.append(detail)
        return GateResult(passed=len(failed) == 0, failed_checks=failed, passed_checks=passed)

    def run_skip(self) -> GateResult:
        return GateResult(passed=True, failed_checks=[], passed_checks=["skipped"])

    @staticmethod
    def error_response(result: GateResult) -> dict[str, Any]:
        if result.passed:
            return {"error_code": None}
        return {"error_code": ErrorCode.EVID_2001.value, "detail": result.failed_checks}

    @staticmethod
    def check_async_completion(*, async_tasks_complete: bool) -> bool:
        return async_tasks_complete

    @staticmethod
    def validate_artifact_status(*, status: str) -> bool:
        return status == "complete"
