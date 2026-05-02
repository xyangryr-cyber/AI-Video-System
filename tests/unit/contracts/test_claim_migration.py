"""Migration-layer tests for [SPEC-A-100] Claim/VerificationRecord.

Covers AC-3 (tables + indexes + FK) and AC-4 (v3.15 `data_point_id`
forward-compat as `claim_id`).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATION_PATH = REPO_ROOT / "migrations" / "V002__create_claim_tables.sql"


def _apply_migration() -> sqlite3.Connection:
    assert MIGRATION_PATH.exists(), f"migration missing at {MIGRATION_PATH}"
    ddl = MIGRATION_PATH.read_text(encoding="utf-8")
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(ddl)
    return conn


class TestAC3MigrationCreatesTables:
    """AC-3: DDL creates claims + verification_records with indexes and FK."""

    def test_migration_creates_claims_and_verification_records_tables(self) -> None:
        conn = _apply_migration()

        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        }
        assert "claims" in tables, f"claims table missing (got {tables})"
        assert "verification_records" in tables, (
            f"verification_records table missing (got {tables})"
        )

        indexes = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' "
                "AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        }
        assert "idx_claims_source_phase_status" in indexes, (
            f"missing composite index on claims (got {indexes})"
        )
        assert "idx_verification_records_claim_id" in indexes, (
            f"missing FK index on verification_records (got {indexes})"
        )

        # FK enforcement: verification_records.claim_id -> claims.claim_id
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO verification_records "
                "(verification_id, claim_id, verifier_type, checked_at, verdict) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    "ver_orphan",
                    "claim_missing",
                    "fact_check_agent",
                    "2026-04-20T00:00:00Z",
                    "verified",
                ),
            )


class TestAC4LegacyDataPointIdPreserved:
    """AC-4: v3.15 `key_data_points.data_point_id` (dp_*) must remain a legal claim_id."""

    def test_migration_preserves_v315_data_point_id_as_claim_id(self) -> None:
        conn = _apply_migration()

        # Accept legacy `dp_*` IDs so old key_data_points can be lifted into claims.
        conn.execute(
            "INSERT INTO claims "
            "(claim_id, claim_type, text, source_phase, source_artifact, "
            "blocking_level, verification_status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "dp_12",
                "data",
                "Gold price 3421.5 USD",
                "P2",
                "polished_script.json",
                "soft",
                "pending",
                "2026-04-20T00:00:00Z",
                "2026-04-20T00:00:00Z",
            ),
        )
        row = conn.execute(
            "SELECT claim_id FROM claims WHERE claim_id=?", ("dp_12",)
        ).fetchone()
        assert row == ("dp_12",), f"legacy dp_* id did not round-trip (got {row})"

        # Pydantic model must also accept legacy `dp_*` IDs.
        from src.shared.schemas.claim import Claim

        legacy = Claim(
            claim_id="dp_12",
            claim_type="data",
            text="Gold price 3421.5 USD",
            source_phase="P2",
            source_artifact="polished_script.json",
            blocking_level="soft",
            verification_status="pending",
            created_at="2026-04-20T00:00:00Z",
            updated_at="2026-04-20T00:00:00Z",
        )
        assert legacy.claim_id == "dp_12"
