"""[SPEC-D-100] Claim verification checks for P8/P10/P11 gates.

Authority: docs/specs/SPEC-D-pipeline-phases.md §D-BDD-1

Provides two check functions:
- check_shot_claims_verified: per-shot claim verification (P8)
- check_hard_claims_verified: hard blocking claim verification (P10/P11)
"""

from __future__ import annotations

from typing import Any, Dict, List


def check_shot_claims_verified(
    *,
    claim_statuses: Dict[str, str],
    shot_claim_refs: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Check per-shot claim_refs. Returns blocked_shots for shots with any unverified claim.

    For P8: shots with unverified claims are skipped individually, not block the entire gate.
    """
    blocked_shots: List[str] = []

    for shot_ref in shot_claim_refs:
        shot_id = shot_ref["shot_id"]
        claim_refs = shot_ref.get("claim_refs", [])
        for cid in claim_refs:
            status = claim_statuses.get(cid, "pending")
            if status not in ("verified",):
                blocked_shots.append(shot_id)
                break

    return {
        "passed": True,  # P8 does not block on claim issues, just skips shots
        "blocked_shots": blocked_shots,
        "has_skips": len(blocked_shots) > 0,
        "failed_checks": (
            [f"claims unverified for shots: {blocked_shots}"] if blocked_shots else []
        ),
        "passed_checks": ([] if blocked_shots else ["all shot claims verified"]),
    }


def check_hard_claims_verified(
    *,
    claim_statuses: Dict[str, str],
    hard_claim_ids: List[str],
) -> Dict[str, Any]:
    """Check that all hard blocking claims are verified.

    For P10/P11: if any hard claim is not verified, the gate returns BLOCK + alert event.
    """
    failed_claims: List[str] = []

    for cid in hard_claim_ids:
        status = claim_statuses.get(cid, "pending")
        if status not in ("verified",):
            failed_claims.append(cid)

    all_pass = len(failed_claims) == 0
    unverified_count = len(failed_claims)

    result: Dict[str, Any] = {
        "passed": all_pass,
        "verdict": "PASS" if all_pass else "BLOCK",
        "failed_claims": failed_claims,
        "failed_checks": (
            [] if all_pass else [f"unverified hard claims: {failed_claims}"]
        ),
        "passed_checks": (
            [f"{len(hard_claim_ids)} hard claims verified"] if all_pass else []
        ),
        "alert_event": (
            None
            if all_pass
            else {
                "type": "claim.block",
                "unverified_count": unverified_count,
                "claim_ids": failed_claims,
                "severity": "P0",
            }
        ),
    }
    return result


__all__ = ["check_hard_claims_verified", "check_shot_claims_verified"]
