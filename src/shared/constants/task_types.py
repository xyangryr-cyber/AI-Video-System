"""[SPEC-A-104] task_ledger.type enum + BDD idempotency rules.

Authority: docs/specs/SPEC-A-contracts.md §A-BDD-5 (SPEC-1B task_ledger
CHECK). Keep in lockstep with ``src/shared/types/task_types.ts`` and the
``V{NNN}__extend_task_ledger_types.sql`` migration.

The v3.16 BDD extension grows the enum from 9 (v3.15) to 15 values by
adding six user-driven actions:

    challenge_claim / supplement_claim / request_chart
    view_phase_detail / save_stage_preference / insert_section

``view_phase_detail`` is audit-only (never persisted to ``task_ledger``);
the other five are persisted with the idempotency semantics in
``IDEMPOTENCY_RULES`` below.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

# v3.15 baseline (9 types). Order matches SPEC-A-contracts.md §SPEC-1B.
_V315_TYPES: tuple[str, ...] = (
    "generate_artifact",
    "regenerate_section",
    "regenerate_shot",
    "user_revision",
    "review",
    "research",
    "verify",
    "cross_check",
    "user_annotation",
)

# v3.16 BDD additions (6 types). Order matches SPEC §A-BDD-5 lines 1107-1114.
_V316_ADDITIONS: tuple[str, ...] = (
    "challenge_claim",
    "supplement_claim",
    "request_chart",
    "view_phase_detail",
    "save_stage_preference",
    "insert_section",
)

TASK_LEDGER_TYPES: tuple[str, ...] = _V315_TYPES + _V316_ADDITIONS


@dataclass(frozen=True)
class IdempotencyRule:
    """Per-action idempotency semantics for new v3.16 task_ledger types.

    - ``persist=False`` -> action is audit-only, never written to
      ``task_ledger`` (view_phase_detail).
    - Empty ``key_fields`` on a persisted action -> no dedup; every call
      creates a new row (supplement_claim / insert_section).
    - ``ttl_hours`` is the idempotency window; ``None`` means permanent
      once the key is written.
    - ``upsert=True`` -> on conflict, overwrite rather than reject
      (save_stage_preference, matching the stage_preferences UNIQUE
      constraint from V003).
    """

    persist: bool = True
    key_fields: tuple[str, ...] = ()
    ttl_hours: int | None = None
    upsert: bool = False


_RULES: dict[str, IdempotencyRule] = {
    # Audit-only: SPEC §A-BDD-5 idempotency table line 1121.
    "view_phase_detail": IdempotencyRule(persist=False),
    # Same (claim_id, evidence) within 24h is idempotent.
    "challenge_claim": IdempotencyRule(
        key_fields=("claim_id", "evidence_hash"),
        ttl_hours=24,
    ),
    # No idempotency -- every supplement creates a new claim.
    "supplement_claim": IdempotencyRule(),
    # Same request_id is idempotent (permanent).
    "request_chart": IdempotencyRule(key_fields=("request_id",)),
    # UPSERT on (project_id, stage, key) matches stage_preferences UNIQUE.
    "save_stage_preference": IdempotencyRule(
        key_fields=("project_id", "stage", "key"),
        upsert=True,
    ),
    # No idempotency -- every insert creates a new section op.
    "insert_section": IdempotencyRule(),
}

IDEMPOTENCY_RULES: Mapping[str, IdempotencyRule] = MappingProxyType(_RULES)


__all__ = [
    "TASK_LEDGER_TYPES",
    "IdempotencyRule",
    "IDEMPOTENCY_RULES",
]
