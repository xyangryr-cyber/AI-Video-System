"""[SPEC-D-009] Gate-P11: validates P11, marks project as completed on pass.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.11.7
"""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List

from src.backend.gates.base_gate import GateResult


class GateP11:
    @staticmethod
    def check(
        *,
        final_cut_exists: bool,
        reviewer_passed: bool,
        audit_clean: bool,
        pending_tasks: List[Any],
        preferences_confirmed: bool,
    ) -> Dict[str, Any]:
        failed: list[str] = []
        passed: list[str] = []

        if not final_cut_exists:
            failed.append("final_cut missing")
        else:
            passed.append("final_cut exists")

        if not reviewer_passed:
            failed.append("FinalReviewer FAIL")
        else:
            passed.append("FinalReviewer PASS")

        if not audit_clean:
            failed.append("audit #3 has inconsistencies")
        else:
            passed.append("audit #3 clean")

        if pending_tasks:
            failed.append(f"{len(pending_tasks)} pending tasks")
        else:
            passed.append("no pending tasks")

        if not preferences_confirmed:
            failed.append("preferences not confirmed")
        else:
            passed.append("preferences confirmed")

        all_pass = len(failed) == 0
        return {
            "passed": all_pass,
            "failed_checks": failed,
            "passed_checks": passed,
            "project_completed": all_pass,
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
