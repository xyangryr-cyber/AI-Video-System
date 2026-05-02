"""[SPEC-D-007] Gate-P8: validates P8 outputs before advancing to P9.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.8.7
"""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List

from src.backend.gates.base_gate import GateResult

_MAX_DEGRADED_SHOTS = 3


class GateP8:
    @staticmethod
    def check(
        *,
        renders_complete: bool,
        degraded_shots: int,
        reviewer_passed: bool,
        pending_tasks: List[Any],
        preferences_confirmed: bool,
    ) -> Dict[str, Any]:
        failed: list[str] = []
        passed: list[str] = []

        if not renders_complete:
            failed.append("renders not complete")
        else:
            passed.append("renders complete")

        if degraded_shots > _MAX_DEGRADED_SHOTS:
            failed.append(
                f"{degraded_shots} degraded shots exceeds max {_MAX_DEGRADED_SHOTS}"
            )
        else:
            passed.append(f"degraded shots ({degraded_shots}) within limit")

        if not reviewer_passed:
            failed.append("VisualReviewer FAIL")
        else:
            passed.append("VisualReviewer PASS")

        if pending_tasks:
            failed.append(f"{len(pending_tasks)} pending tasks")
        else:
            passed.append("no pending tasks")

        if not preferences_confirmed:
            failed.append("preferences not confirmed")
        else:
            passed.append("preferences confirmed")

        return {
            "passed": len(failed) == 0,
            "failed_checks": failed,
            "passed_checks": passed,
        }

    # -- v3.17 extension (D-022) --

    @staticmethod
    def check_v317(
        *,
        renders_complete: bool = False,
        material_readiness: bool = False,
        degraded_shots: int = 0,
        reviewer_passed: bool = False,
    ) -> Dict[str, Any]:
        failed: list[str] = []
        passed: list[str] = []

        if not renders_complete:
            failed.append("renders not complete")
        else:
            passed.append("renders complete")

        if not material_readiness:
            failed.append("material readiness not verified")
        else:
            passed.append("material readiness verified")

        if degraded_shots > _MAX_DEGRADED_SHOTS:
            failed.append(f"{degraded_shots} degraded shots")
        else:
            passed.append(f"degraded shots ({degraded_shots}) ok")

        if not reviewer_passed:
            failed.append("VisualReviewer FAIL")
        else:
            passed.append("VisualReviewer PASS")

        return {
            "passed": len(failed) == 0,
            "failed_checks": failed,
            "passed_checks": passed,
        }


def check_hard_claims(
    project_id: str,
    conn: sqlite3.Connection,
) -> GateResult:
    """Verify all hard claims for the project are verified.

    Queries the claims table for claims with blocking_level='hard'.
    If no hard claims exist, returns PASS.
    If any hard claim has verification_status != 'verified', returns FAIL.
    """
    rows = conn.execute(
        "SELECT claim_id, verification_status FROM claims WHERE blocking_level = 'hard'"
    ).fetchall()

    if not rows:
        return GateResult(
            passed=True,
            passed_checks=["no hard claims found for project"],
        )

    failed = []
    passed = []
    for row in rows:
        cid = row[0] if not hasattr(row, "keys") else row["claim_id"]
        status = row[1] if not hasattr(row, "keys") else row["verification_status"]
        if status == "verified":
            passed.append(f"claim {cid} verified")
        else:
            failed.append(f"claim {cid} status={status}")

    return GateResult(
        passed=len(failed) == 0,
        failed_checks=failed,
        passed_checks=passed,
    )
