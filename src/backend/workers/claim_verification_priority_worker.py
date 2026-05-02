"""[SPEC-B-100] High-priority claim_verification worker for challenge_claim.

Authority: SPEC-B §B-BDD-1.1 (v3.16). Task card B-100 §AC-4.

Handles user-triggered ``challenge_claim`` re-verification on a dedicated
``claim_verification_priority`` queue so standard verification backlog
cannot block user-facing challenges. Retry/dead-letter policy is the same
as the normal worker (SPEC-B-BDD-1.1); only the queue priority and the
latency budget differ.
"""

from __future__ import annotations

from src.backend.workers.claim_verification_worker import (
    MAX_ATTEMPTS,
    RETRY_DELAYS_SEC,
    handle_failure,
)


QUEUE_NAME: str = "claim_verification_priority"
QUEUE_PRIORITY: str = "high"

# SPEC-B-100 AC-4: challenge_claim latency p95 MUST be < 30s.
PRIORITY_LATENCY_BUDGET_P95_SEC: int = 30


def compute_p95_latency(samples: list[float]) -> float:
    """Return the 95th-percentile latency across ``samples`` (seconds).

    Uses the nearest-rank method (no numpy dependency): sort ascending,
    pick the sample at index ceil(0.95*N)-1.
    """
    if not samples:
        raise ValueError("samples must be non-empty")
    ordered = sorted(samples)
    n = len(ordered)
    # nearest-rank: idx = ceil(0.95 * n) - 1 (0-based)
    idx = max(0, -(-(95 * n) // 100) - 1)
    return float(ordered[idx])


def is_priority_latency_within_budget(samples: list[float]) -> bool:
    """True iff p95(samples) < PRIORITY_LATENCY_BUDGET_P95_SEC."""
    return compute_p95_latency(samples) < PRIORITY_LATENCY_BUDGET_P95_SEC


__all__ = [
    "QUEUE_NAME",
    "QUEUE_PRIORITY",
    "PRIORITY_LATENCY_BUDGET_P95_SEC",
    "MAX_ATTEMPTS",
    "RETRY_DELAYS_SEC",
    "handle_failure",
    "compute_p95_latency",
    "is_priority_latency_within_budget",
]
