// [SPEC-A-104] task_ledger.type enum + BDD idempotency rules.
// Authority: docs/specs/SPEC-A-contracts.md §A-BDD-5 (SPEC-1B task_ledger
// CHECK). Keep in lockstep with src/shared/constants/task_types.py and the
// V{NNN}__extend_task_ledger_types.sql migration.
//
// The v3.16 BDD extension grows the enum from 9 (v3.15) to 15 values by
// adding six user-driven actions. view_phase_detail is audit-only (never
// persisted to task_ledger); the other five are persisted with the
// idempotency semantics in IDEMPOTENCY_RULES below.

export const TASK_LEDGER_TYPES = [
  // v3.15 baseline (9)
  "generate_artifact",
  "regenerate_section",
  "regenerate_shot",
  "user_revision",
  "review",
  "research",
  "verify",
  "cross_check",
  "user_annotation",
  // v3.16 BDD additions (6)
  "challenge_claim",
  "supplement_claim",
  "request_chart",
  "view_phase_detail",
  "save_stage_preference",
  "insert_section",
] as const;

export type TaskLedgerType = (typeof TASK_LEDGER_TYPES)[number];

// Per-action idempotency semantics for new v3.16 task_ledger types.
// - persist=false -> action is audit-only, never written to task_ledger.
// - Empty key_fields on a persisted action -> no dedup.
// - ttl_hours is the idempotency window; null means permanent.
// - upsert=true -> on conflict, overwrite rather than reject.
export interface IdempotencyRule {
  persist: boolean;
  key_fields: readonly string[];
  ttl_hours: number | null;
  upsert: boolean;
}

export const IDEMPOTENCY_RULES: Readonly<Record<string, IdempotencyRule>> = {
  view_phase_detail: {
    persist: false,
    key_fields: [],
    ttl_hours: null,
    upsert: false,
  },
  challenge_claim: {
    persist: true,
    key_fields: ["claim_id", "evidence_hash"],
    ttl_hours: 24,
    upsert: false,
  },
  supplement_claim: {
    persist: true,
    key_fields: [],
    ttl_hours: null,
    upsert: false,
  },
  request_chart: {
    persist: true,
    key_fields: ["request_id"],
    ttl_hours: null,
    upsert: false,
  },
  save_stage_preference: {
    persist: true,
    key_fields: ["project_id", "stage", "key"],
    ttl_hours: null,
    upsert: true,
  },
  insert_section: {
    persist: true,
    key_fields: [],
    ttl_hours: null,
    upsert: false,
  },
} as const;
