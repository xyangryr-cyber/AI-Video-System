-- [SPEC-A-104] V005: extend task_ledger.type to the v3.16 BDD enum.
-- Authority: docs/specs/SPEC-A-contracts.md §A-BDD-5 (SPEC-1B task_ledger).
--
-- SQLite cannot ALTER a CHECK constraint in place, so we follow the canonical
-- rebuild pattern:
--   1. rename the existing task_ledger out of the way
--   2. create a new task_ledger with the 15-value CHECK (9 v3.15 + 6 v3.16)
--   3. copy legacy rows verbatim (existing data uses v3.15 types only, so
--      the new CHECK accepts them unchanged -- AC-3 "legacy data compatible")
--   4. remove the renamed legacy table
--
-- Foreign keys that reference task_ledger(id) (e.g. async_tasks.ledger_task_id)
-- stay intact because we keep the same table name after the swap. We
-- temporarily disable FK checks during the rebuild per the SQLite
-- documented 12-step pattern.

PRAGMA foreign_keys = OFF;

ALTER TABLE task_ledger RENAME TO task_ledger__v315;

CREATE TABLE task_ledger (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    phase INTEGER NOT NULL,
    type TEXT NOT NULL CHECK(type IN (
        -- v3.15 baseline (9)
        'generate_artifact',
        'regenerate_section',
        'regenerate_shot',
        'user_revision',
        'review',
        'research',
        'verify',
        'cross_check',
        'user_annotation',
        -- v3.16 BDD additions (6)
        'challenge_claim',
        'supplement_claim',
        'request_chart',
        'view_phase_detail',
        'save_stage_preference',
        'insert_section'
    )),
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN (
        'pending','queued','running','succeeded','failed','superseded','timeout'
    )),
    depends_on TEXT,
    produces_version INTEGER,
    target_version INTEGER,
    params TEXT NOT NULL DEFAULT '{}',
    result_ref TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

INSERT INTO task_ledger (
    id, project_id, phase, type, status, depends_on,
    produces_version, target_version, params, result_ref,
    created_at, updated_at
)
SELECT
    id, project_id, phase, type, status, depends_on,
    produces_version, target_version, params, result_ref,
    created_at, updated_at
FROM task_ledger__v315;

DROP TABLE task_ledger__v315;

PRAGMA foreign_keys = ON;
