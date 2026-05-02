"""[SPEC-D-001] Reviewer verdict / Gate failure response bindings.

Authority:
  - docs/specs/SPEC-D-pipeline-phases.md "Reviewer / Gate / Verdict unified binding"
  - src/shared/constants/error_codes.py (ErrorCode.EVID_2001)
"""

from __future__ import annotations

from typing import Any

from src.shared.constants.error_codes import HTTP_STATUS_BY_CODE, ErrorCode
from src.shared.types.verdict import Verdict


def build_gate_failure_response(
    *,
    failed_checks: list[str],
    passed_checks: list[str],
) -> dict[str, Any]:
    """Build the standard gate failure response with EVID_2001.

    Returns a dict with *error_code*, *http_status*, *failed_checks*,
    and *passed_checks*, matching the SPEC-D / SPEC-A SPEC-13A contract.
    """
    return {
        "error_code": ErrorCode.EVID_2001.value,
        "http_status": HTTP_STATUS_BY_CODE[ErrorCode.EVID_2001],
        "failed_checks": list(failed_checks),
        "passed_checks": list(passed_checks),
    }


def compute_review_status(task_ledger: list[dict[str, Any]]) -> str:
    """Pure function: compute review_status from task_ledger entries.

    Returns one of ``pending``, ``in_progress``, ``passed``, ``failed``.

    Rules (per SPEC-A SPEC-0A.3):
      - No review tasks in ledger -> ``pending``
      - Any review task with status != done -> ``in_progress``
      - All review tasks done + all PASS -> ``passed``
      - Any review task done + FAIL -> ``failed``
    """
    reviews = [t for t in task_ledger if t.get("task_type") == "review"]
    if not reviews:
        return "pending"

    for r in reviews:
        if r.get("status") not in (None, "done", "completed"):
            return "in_progress"

    for r in reviews:
        if r.get("verdict") == "FAIL":
            return "failed"

    return "passed"


__all__ = ["Verdict", "build_gate_failure_response", "compute_review_status"]
