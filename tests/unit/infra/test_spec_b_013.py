"""Tests for [SPEC-B-013] SQLite migration: projects.master_audio_ref."""

import json
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
V006_SQL = REPO_ROOT / "scripts" / "migrations" / "V006__add_master_audio_ref.sql"


def _fresh_conn() -> sqlite3.Connection:
    """In-memory DB with v1 baseline schema applied."""
    init_sql = REPO_ROOT / "src" / "backend" / "db" / "migrations" / "001_initial.sql"
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(init_sql.read_text(encoding="utf-8"))
    return conn


def _apply_v006(conn: sqlite3.Connection) -> None:
    sql = V006_SQL.read_text(encoding="utf-8")
    marker = "-- ROLLBACK"
    forward = sql[: sql.index(marker)]
    conn.executescript(forward)


_VALID_JSON = json.dumps(
    {
        "kind": "narration_master",
        "file_path": "phase_4/narration_master.mp3",
        "based_on_phase": 4,
        "checksum": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "version": 1,
    }
)


class TestAC4:
    """AC-4: Insert valid master_audio_ref JSON, read back, pass
    A-013 MasterAudioRef schema validation."""

    def test_insert_valid_master_audio_ref(self):
        conn = _fresh_conn()
        _apply_v006(conn)
        conn.execute(
            "INSERT INTO projects (project_id, title, description) VALUES (?, ?, ?)",
            ("proj_test_ac4", "test", "desc"),
        )
        conn.execute(
            "UPDATE projects SET master_audio_ref = ? WHERE project_id = ?",
            (_VALID_JSON, "proj_test_ac4"),
        )
        conn.commit()
        row = conn.execute(
            "SELECT master_audio_ref FROM projects WHERE project_id = ?",
            ("proj_test_ac4",),
        ).fetchone()
        assert row is not None
        assert row["master_audio_ref"] is not None

    def test_read_back_passes_schema(self):
        conn = _fresh_conn()
        _apply_v006(conn)
        conn.execute(
            "INSERT INTO projects (project_id, title, description) VALUES (?, ?, ?)",
            ("proj_test_schema", "test", "desc"),
        )
        conn.execute(
            "UPDATE projects SET master_audio_ref = ? WHERE project_id = ?",
            (_VALID_JSON, "proj_test_schema"),
        )
        conn.commit()
        row = conn.execute(
            "SELECT master_audio_ref FROM projects WHERE project_id = ?",
            ("proj_test_schema",),
        ).fetchone()
        raw = row["master_audio_ref"]
        obj = json.loads(raw)
        assert obj["kind"] == "narration_master"
        assert obj["file_path"].startswith("phase_")
        assert obj["based_on_phase"] in (4, 5, 6)
        assert obj["checksum"].startswith("sha256:")
        assert len(obj["checksum"]) == 71  # sha256: + 64 hex
        assert obj["version"] >= 1

        # Validate through A-013 schema (Pydantic)
        from src.shared.schemas.project_state import MasterAudioRef

        parsed = MasterAudioRef.model_validate(obj)
        assert parsed.kind == "narration_master"
        assert parsed.based_on_phase == 4
        assert parsed.version == 1


class TestAC5:
    """AC-5: Migration tests live in CI unit suite alongside other
    migration tests."""

    def test_migration_in_ci_unit_suite(self):
        migration_test = (
            REPO_ROOT / "scripts" / "migrations" / "test_migration_master_audio_ref.py"
        )
        assert migration_test.exists(), (
            "AC-5: migration test file must exist in scripts/migrations/"
        )
        content = migration_test.read_text(encoding="utf-8")
        assert "test_forward_adds_column" in content
        assert "test_rollback_drops_column_and_index" in content
        assert "test_forward_rollback_forward_idempotent" in content


class TestAC6:
    """AC-6: Migration SQL documents table-level ownership hint
    (writers/readers/write-timing) in comments."""

    def test_table_level_ownership_hint_documented(self):
        sql = V006_SQL.read_text(encoding="utf-8")
        assert "NarrationMasterAssembler" in sql, (
            "AC-6: must document NarrationMasterAssembler as writer"
        )
        assert "BgmMixRenderer" in sql
        assert "FinalAudioAssembler" in sql
        assert "Gate 4" in sql and "Gate 5" in sql and "Gate 6" in sql, (
            "AC-6: must document write timing per gate"
        )
