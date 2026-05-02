"""Integration tests for [SPEC-B-013] projects.master_audio_ref column.

Authority:
  tasks/SPEC-B/B-013-master-audio-ref-migration.md Test Mapping AC-4..AC-6.

Covers:
  AC-4: insert valid JSON into projects.master_audio_ref + read back and
        validate through the SPEC-A-013 `MasterAudioRef` Pydantic schema.
  AC-5: the migration test file (scripts/migrations/test_migration_master_audio_ref.py)
        is collectable by pytest as a unit test, i.e. lives in a directory
        pytest discovers alongside tests/unit/infra/.
  AC-6: the V006 migration carries a SPEC-1B table-level ownership hint
        (NarrationMasterAssembler / BgmMixRenderer / FinalAudioAssembler
        writers; Gate 4/5/6 write timing) in its comment header, for the
        docs PR to lift verbatim (task card declares docs out of scope).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATION_PATH = REPO_ROOT / "scripts" / "migrations" / "V006__add_master_audio_ref.sql"
MIGRATION_TEST_PATH = (
    REPO_ROOT / "scripts" / "migrations" / "test_migration_master_audio_ref.py"
)
V1_CORE_INITIAL = (
    REPO_ROOT / "src" / "backend" / "db" / "migrations" / "001_initial.sql"
)
ROLLBACK_MARKER = "-- ROLLBACK"
OWNERSHIP_HINT_TOKENS = (
    "NarrationMasterAssembler",
    "BgmMixRenderer",
    "FinalAudioAssembler",
    "Gate 4",
    "Gate 5",
    "Gate 6",
)


def _forward_sql() -> str:
    text = MIGRATION_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()
    cut = next(
        (
            i
            for i, line in enumerate(lines)
            if line.lstrip().startswith(ROLLBACK_MARKER)
        ),
        None,
    )
    assert cut is not None, "migration missing ROLLBACK marker"
    return "\n".join(lines[:cut])


def _apply_forward() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(V1_CORE_INITIAL.read_text(encoding="utf-8"))
    conn.executescript(_forward_sql())
    conn.execute(
        "INSERT INTO projects(project_id, title, description) "
        "VALUES ('proj_001', 't', 'd')"
    )
    return conn


# ---------------------------------------------------------------------------


class TestAC4InsertAndRoundTripSchema:
    """AC-4: insert valid JSON + read back validates against A-013 schema."""

    def test_insert_valid_master_audio_ref(self) -> None:
        conn = _apply_forward()
        payload = {
            "kind": "narration_master",
            "file_path": "phase_4/narration_master.mp3",
            "based_on_phase": 4,
            "checksum": "sha256:" + "a" * 64,
            "version": 1,
        }
        conn.execute(
            "UPDATE projects SET master_audio_ref=? WHERE project_id=?",
            (json.dumps(payload), "proj_001"),
        )
        # The expression index must yield based_on_phase=4 for this row.
        row = conn.execute(
            "SELECT json_extract(master_audio_ref, '$.based_on_phase') "
            "FROM projects WHERE project_id=?",
            ("proj_001",),
        ).fetchone()
        assert row[0] == 4

    def test_read_back_passes_schema(self) -> None:
        from src.shared.schemas.project_state import MasterAudioRef

        conn = _apply_forward()
        payload = {
            "kind": "narration_master",
            "file_path": "phase_4/narration_master.mp3",
            "based_on_phase": 4,
            "checksum": "sha256:" + "b" * 64,
            "version": 1,
        }
        conn.execute(
            "UPDATE projects SET master_audio_ref=? WHERE project_id=?",
            (json.dumps(payload), "proj_001"),
        )
        stored = conn.execute(
            "SELECT master_audio_ref FROM projects WHERE project_id=?",
            ("proj_001",),
        ).fetchone()[0]
        # Schema validates the round-tripped JSON.
        model = MasterAudioRef.model_validate_json(stored)
        assert model.kind == "narration_master"
        assert model.based_on_phase == 4
        assert model.version == 1
        assert model.checksum.startswith("sha256:")
        # Legacy rows must stay NULL and never hit the validator.
        conn.execute(
            "INSERT INTO projects(project_id, title, description) "
            "VALUES ('proj_legacy', 't', 'd')"
        )
        legacy = conn.execute(
            "SELECT master_audio_ref FROM projects WHERE project_id=?",
            ("proj_legacy",),
        ).fetchone()[0]
        assert legacy is None


class TestAC5MigrationInCiUnitSuite:
    """AC-5: migration test file is collectable alongside infra tests."""

    def test_migration_in_ci_unit_suite(self) -> None:
        # The dedicated migration-level test lives under scripts/migrations/
        # and uses pytest's standard `test_` prefix so the CI command
        # `pytest scripts/migrations/ tests/unit/infra/` picks it up.
        assert MIGRATION_TEST_PATH.exists(), (
            f"migration test missing: {MIGRATION_TEST_PATH}"
        )
        assert MIGRATION_TEST_PATH.name.startswith("test_"), (
            "migration test filename must start with 'test_' for pytest"
        )
        # This very file must live under tests/unit/infra/ so CI picks it
        # up alongside the other infra migration regressions (AC-5).
        here = Path(__file__).resolve().relative_to(REPO_ROOT)
        assert here.parts[:3] == ("tests", "unit", "infra"), (
            f"expected this test under tests/unit/infra/; got {here}"
        )


class TestAC6OwnershipHintDocumented:
    """AC-6: migration carries the SPEC-1B ownership diff hint."""

    def test_table_level_ownership_hint_documented(self) -> None:
        sql = MIGRATION_PATH.read_text(encoding="utf-8")
        for token in OWNERSHIP_HINT_TOKENS:
            assert token in sql, (
                f"migration header must name ownership hint token {token!r} "
                f"for the SPEC-1B doc PR to lift"
            )
        # The hint must sit inside `--` comments so executescript() ignores
        # it; otherwise AC-1/AC-3 `executescript` would fail with a syntax
        # error the moment these tokens appeared as SQL identifiers.
        for token in OWNERSHIP_HINT_TOKENS:
            in_comment = any(
                token in line and line.lstrip().startswith("--")
                for line in sql.splitlines()
            )
            assert in_comment, (
                f"ownership hint token {token!r} must live inside `-- ` "
                f"comment lines (otherwise SQL would choke on it)"
            )
