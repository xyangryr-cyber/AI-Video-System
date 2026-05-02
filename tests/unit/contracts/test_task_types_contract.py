"""Shared test implementations for [SPEC-A-104] task_ledger.type BDD extension.

Authority: docs/specs/SPEC-A-contracts.md §A-BDD-5 (SPEC-1B task_ledger CHECK).

Covers AC-1..AC-3. Re-exported by ``test_spec_a_104.py`` (A-100 / A-101 /
A-102 / A-103 pattern) so the task-card ``verification_commands``
(``pytest tests/unit/contracts/test_spec_a_104.py -v``) runs the real
assertions rather than the prior ``pytest.skip`` stubs.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS_DIR = REPO_ROOT / "migrations"
V1_CORE_INITIAL = (
    REPO_ROOT / "src" / "backend" / "db" / "migrations" / "001_initial.sql"
)
TS_PATH = REPO_ROOT / "src" / "shared" / "types" / "task_types.ts"

# v3.15 baseline (9 types); see SPEC-A-contracts.md line 450-453 + A-REV-3.
V315_TYPES = (
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

# v3.16 additions (6 types); see SPEC-A-contracts.md §A-BDD-5 lines 1107-1114.
V316_ADDITIONS = (
    "challenge_claim",
    "supplement_claim",
    "request_chart",
    "view_phase_detail",
    "save_stage_preference",
    "insert_section",
)


def _v104_migration_path() -> Path:
    """Return the V{NNN}__extend_task_ledger_types.sql (any NNN >= 005)."""
    matches = sorted(MIGRATIONS_DIR.glob("V*__extend_task_ledger_types.sql"))
    assert matches, (
        f"task_ledger extend migration missing under {MIGRATIONS_DIR} "
        f"(expected V{{NNN}}__extend_task_ledger_types.sql)"
    )
    return matches[-1]


def _apply_migration() -> sqlite3.Connection:
    """Create v1-core tables then apply the V005 extend migration.

    Uses the actual `src/backend/db/migrations/001_initial.sql` as the baseline
    so the V005 rebuild pattern runs against the same `task_ledger` shape it
    will rebuild in prod (AC-3 realism).
    """
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(V1_CORE_INITIAL.read_text(encoding="utf-8"))
    conn.execute(
        "INSERT INTO projects(project_id, title, description) "
        "VALUES ('proj_001', 'p1', 'd1')"
    )
    # Seed a legacy row using an existing v3.15 type -- must survive migration.
    conn.execute(
        "INSERT INTO task_ledger(id, project_id, phase, type) "
        "VALUES ('t_000001', 'proj_001', 2, 'generate_artifact')"
    )
    conn.executescript(_v104_migration_path().read_text(encoding="utf-8"))
    return conn


class TestAC1TaskLedgerTypeEnumAppendsSix:
    """AC-1: type enum gains the 6 BDD actions on top of the v3.15 9-tuple."""

    def test_task_ledger_type_enum_appends_six_bdd_actions(self) -> None:
        from src.shared.constants.task_types import TASK_LEDGER_TYPES

        # All v3.16 additions present.
        missing = [t for t in V316_ADDITIONS if t not in TASK_LEDGER_TYPES]
        assert not missing, (
            f"TASK_LEDGER_TYPES missing v3.16 additions: {missing} "
            f"(have {TASK_LEDGER_TYPES})"
        )

        # All v3.15 baseline types preserved (no regression).
        missing = [t for t in V315_TYPES if t not in TASK_LEDGER_TYPES]
        assert not missing, (
            f"TASK_LEDGER_TYPES dropped v3.15 baseline: {missing} "
            f"(have {TASK_LEDGER_TYPES})"
        )

    def test_ts_mirror_lists_same_fifteen_types(self) -> None:
        assert TS_PATH.exists(), f"missing TS file: {TS_PATH}"
        src = TS_PATH.read_text(encoding="utf-8")
        for t in V315_TYPES + V316_ADDITIONS:
            assert f'"{t}"' in src, f'task_types.ts missing literal "{t}"'


class TestAC2FifteenWithIdempotencyKeysForNewSix:
    """AC-2: total enum is 15 and new 6 each have an idempotency rule."""

    def test_task_types_total_fifteen_with_idempotency_keys_for_new_six(self) -> None:
        from src.shared.constants.task_types import (
            IDEMPOTENCY_RULES,
            TASK_LEDGER_TYPES,
        )

        assert len(TASK_LEDGER_TYPES) == 15, (
            f"expected exactly 15 task_ledger types; got "
            f"{len(TASK_LEDGER_TYPES)} -> {TASK_LEDGER_TYPES}"
        )
        # No duplicates.
        assert len(set(TASK_LEDGER_TYPES)) == 15, (
            f"TASK_LEDGER_TYPES contains duplicates: {TASK_LEDGER_TYPES}"
        )

        # Every new v3.16 action has an idempotency entry (including the
        # "not persisted" flag for view_phase_detail and the "no idempotency"
        # flag for supplement_claim / insert_section).
        for action in V316_ADDITIONS:
            assert action in IDEMPOTENCY_RULES, (
                f"IDEMPOTENCY_RULES missing {action!r} "
                f"(have {sorted(IDEMPOTENCY_RULES)})"
            )

        # view_phase_detail: audit-only, never persisted to task_ledger.
        assert IDEMPOTENCY_RULES["view_phase_detail"].persist is False, (
            "view_phase_detail must be audit-only (persist=False); see SPEC "
            "§A-BDD-5 idempotency table line 1121."
        )

        # challenge_claim: same (claim_id + evidence) within 24h is idempotent.
        cc = IDEMPOTENCY_RULES["challenge_claim"]
        assert cc.persist is True
        assert "claim_id" in cc.key_fields
        assert any("evidence" in f for f in cc.key_fields), (
            f"challenge_claim must key on evidence (see SPEC §A-BDD-5); "
            f"got key_fields={cc.key_fields}"
        )
        assert cc.ttl_hours == 24, (
            f"challenge_claim TTL must be 24h; got {cc.ttl_hours}"
        )

        # request_chart: same request_id is idempotent.
        rc = IDEMPOTENCY_RULES["request_chart"]
        assert rc.persist is True
        assert rc.key_fields == ("request_id",), (
            f"request_chart key must be (request_id,); got {rc.key_fields}"
        )

        # save_stage_preference: UPSERT on (project_id, stage, key) -- matches
        # the stage_preferences UNIQUE constraint from SPEC-A-101 / V003.
        ssp = IDEMPOTENCY_RULES["save_stage_preference"]
        assert ssp.persist is True
        assert ssp.key_fields == ("project_id", "stage", "key"), (
            f"save_stage_preference key must match stage_preferences "
            f"UNIQUE; got {ssp.key_fields}"
        )
        assert ssp.upsert is True, (
            "save_stage_preference must UPSERT on conflict (SPEC §A-BDD-5)"
        )

        # supplement_claim + insert_section: no idempotency (every call creates
        # a new record); represented by empty key_fields.
        for action in ("supplement_claim", "insert_section"):
            rule = IDEMPOTENCY_RULES[action]
            assert rule.persist is True
            assert rule.key_fields == (), (
                f"{action} must have no idempotency key; got {rule.key_fields}"
            )


class TestAC3MigrationCheckConstraintRejectsUnknownType:
    """AC-3: migration enforces CHECK over the full 15-type enum."""

    def test_migration_applies_and_preserves_legacy_rows(self) -> None:
        conn = _apply_migration()
        rows = conn.execute("SELECT id, type FROM task_ledger ORDER BY id").fetchall()
        assert rows == [("t_000001", "generate_artifact")], (
            f"legacy task_ledger row did not survive rebuild: {rows}"
        )

    def test_migration_check_constraint_accepts_all_fifteen(self) -> None:
        conn = _apply_migration()
        for i, t in enumerate(V315_TYPES + V316_ADDITIONS, start=100):
            conn.execute(
                "INSERT INTO task_ledger(id, project_id, phase, type) "
                "VALUES (?, 'proj_001', 0, ?)",
                (f"t_{i:06d}", t),
            )
        cnt = conn.execute("SELECT COUNT(*) FROM task_ledger").fetchone()[0]
        # 1 legacy row seeded pre-migration + 15 freshly inserted.
        assert cnt == 1 + 15, f"expected 16 rows after all-type insert; got {cnt}"

    def test_migration_check_constraint_rejects_unknown_task_type(self) -> None:
        conn = _apply_migration()
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO task_ledger(id, project_id, phase, type) "
                "VALUES ('t_bogus', 'proj_001', 0, 'not_a_real_type')"
            )
