"""[SPEC-B-100] claim_verification worker — retry/backoff + dead letter.

Authority: SPEC-B §B-BDD-1.1 (v3.16). Task card B-100 §AC-1.

Responsibilities:
- Hold the canonical retry ladder ``(30, 120, 600)`` seconds.
- Decide per-attempt whether to retry (with the matching delay) or send the
  claim to the dead-letter state (``verification_records.verdict='inconclusive'``).

The actual Huey task body (invoking FactCheckAgent / FinancialDataService)
lands in SPEC-C; this module exposes only the policy primitives so B-100's
verification tests, alerting, and Dashboard metrics can exercise them
without importing Huey.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

QUEUE_NAME: str = "claim_verification"
QUEUE_PRIORITY: str = "normal"

# Retry delay ladder (seconds): 30s -> 2m -> 10m, per SPEC-B-BDD-1.1.
RETRY_DELAYS_SEC: tuple[int, int, int] = (30, 120, 600)

# SPEC caps retries at 3 attempts; failure #3 routes to dead letter.
MAX_ATTEMPTS: int = 3

# On exhaustion, write a verification_records row with this verdict.
DEAD_LETTER_VERDICT: str = "inconclusive"


class RetryAction(TypedDict):
    action: Literal["retry"]
    delay_sec: int


class DeadLetterAction(TypedDict):
    action: Literal["dead_letter"]
    verdict: str


def handle_failure(*, attempt: int) -> RetryAction | DeadLetterAction:
    """Return the next action after the *attempt*-th failure.

    ``attempt`` is 1-indexed. Attempts 1..MAX_ATTEMPTS-1 return a
    retry action carrying the matching RETRY_DELAYS_SEC entry; the
    MAX_ATTEMPTS-th failure returns a dead-letter action.
    """
    if attempt < 1:
        raise ValueError(f"attempt must be >= 1, got {attempt}")
    if attempt >= MAX_ATTEMPTS:
        return {"action": "dead_letter", "verdict": DEAD_LETTER_VERDICT}
    return {"action": "retry", "delay_sec": RETRY_DELAYS_SEC[attempt - 1]}


def dead_letter_record(claim_id: str, reason: str) -> dict[str, Any]:
    """Build the verification_records row inserted on dead-letter.

    Kept as a plain dict (not a Pydantic model) so the policy layer
    stays framework-free; callers pass this to the verification_records
    repository when the 3rd attempt fails.
    """
    return {
        "claim_id": claim_id,
        "verdict": DEAD_LETTER_VERDICT,
        "reason": reason or "claim_verification retries exhausted",
    }


__all__ = [
    "QUEUE_NAME",
    "QUEUE_PRIORITY",
    "RETRY_DELAYS_SEC",
    "MAX_ATTEMPTS",
    "DEAD_LETTER_VERDICT",
    "handle_failure",
    "dead_letter_record",
]
