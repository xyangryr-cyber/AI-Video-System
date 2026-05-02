"""[SPEC-B-100] Queue configuration for claim_verification workers.

Authority: SPEC-B §B-BDD-1.1 (v3.16). Task card B-100 §AC-1, AC-4.

Naming note: the task card lists this file as ``celery_config.py`` by
convention (the v3.12 SPEC draft considered Celery). The project actually
runs on Huey (see src/backend/workers/huey_config.py + config/huey_queues.yaml);
this module re-exposes the same queue contract as a framework-agnostic
dict so orchestration code (Huey today, Celery if ever swapped) can
read a single source of truth.
"""
from __future__ import annotations

from src.backend.workers.claim_verification_priority_worker import (
    QUEUE_NAME as PRIORITY_QUEUE_NAME,
    QUEUE_PRIORITY as PRIORITY_QUEUE_PRIORITY,
    PRIORITY_LATENCY_BUDGET_P95_SEC,
)
from src.backend.workers.claim_verification_worker import (
    DEAD_LETTER_VERDICT,
    MAX_ATTEMPTS,
    QUEUE_NAME as STANDARD_QUEUE_NAME,
    QUEUE_PRIORITY as STANDARD_QUEUE_PRIORITY,
    RETRY_DELAYS_SEC,
)


# Environment-variable defaults exposed by docker-compose (see SPEC-B-BDD-1.1):
#   CLAIM_VERIFICATION_RETRY_DELAYS = "30,120,600"
#   CLAIM_VERIFICATION_MAX_ATTEMPTS = "3"
CLAIM_VERIFICATION_RETRY_DELAYS: tuple[int, ...] = RETRY_DELAYS_SEC
CLAIM_VERIFICATION_MAX_ATTEMPTS: int = MAX_ATTEMPTS


QUEUES: dict[str, dict[str, object]] = {
    STANDARD_QUEUE_NAME: {
        "priority": STANDARD_QUEUE_PRIORITY,
        "retry_delays_sec": list(RETRY_DELAYS_SEC),
        "max_attempts": MAX_ATTEMPTS,
        "dead_letter_verdict": DEAD_LETTER_VERDICT,
    },
    PRIORITY_QUEUE_NAME: {
        "priority": PRIORITY_QUEUE_PRIORITY,
        "retry_delays_sec": list(RETRY_DELAYS_SEC),
        "max_attempts": MAX_ATTEMPTS,
        "dead_letter_verdict": DEAD_LETTER_VERDICT,
        "latency_budget_p95_sec": PRIORITY_LATENCY_BUDGET_P95_SEC,
    },
}


__all__ = [
    "CLAIM_VERIFICATION_RETRY_DELAYS",
    "CLAIM_VERIFICATION_MAX_ATTEMPTS",
    "QUEUES",
]
