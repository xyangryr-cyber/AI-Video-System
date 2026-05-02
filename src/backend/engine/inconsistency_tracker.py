"""[SPEC-D-015] InconsistencyTracker -- stores audit inconsistency records.

Authority: docs/specs/SPEC-D-pipeline-phases.md "Inconsistency Tracking"
"""

from __future__ import annotations

from typing import Any


class InconsistencyTracker:
    """Track cross-phase audit inconsistencies with resolution status."""

    def __init__(self) -> None:
        self._records: list[dict[str, Any]] = []

    def record(
        self,
        *,
        audit_id: str,
        phase: int,
        check_name: str,
        expected_value: str,
        actual_value: str,
    ) -> None:
        self._records.append(
            {
                "audit_id": audit_id,
                "phase": phase,
                "check_name": check_name,
                "expected_value": expected_value,
                "actual_value": actual_value,
                "status": "detected",
                "resolved_at": None,
            }
        )

    def resolve(self, *, index: int, status: str) -> None:
        if 0 <= index < len(self._records):
            self._records[index]["status"] = status

    def list_records(self) -> list[dict[str, Any]]:
        return list(self._records)
