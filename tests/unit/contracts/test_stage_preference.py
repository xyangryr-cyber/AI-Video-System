"""Shared test implementations for [SPEC-A-101] StagePreference contracts.

Authority: docs/specs/SPEC-A-contracts.md §A-BDD-2 (SPEC-0A.9).

Covers AC-1..AC-5. Re-exported by ``test_spec_a_101.py`` (A-100 pattern).
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any, Dict

import pytest
from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS_DIR = REPO_ROOT / "migrations"
TS_PATH = REPO_ROOT / "src" / "shared" / "types" / "stage_preference.ts"

SCOPE_VALUES = ("global", "cross_project", "project", "stage")
STAGE_VALUES = (
    "P2_script",
    "P3_polish",
    "P4_tts",
    "P5_bgm",
    "P6_sfx",
    "P7_storyboard",
    "P8_keyframe",
    "P9_broll",
    "P10_roughcut",
    "P11_finalize",
)


def _stage_migration_path() -> Path:
    """Return the V{NNN}__create_stage_preferences.sql (any NNN)."""
    matches = sorted(MIGRATIONS_DIR.glob("V*__create_stage_preferences.sql"))
    assert matches, (
        f"stage_preferences migration missing under {MIGRATIONS_DIR} "
        f"(expected V{{NNN}}__create_stage_preferences.sql)"
    )
    return matches[-1]


def _apply_migration() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    # Minimal `projects` stub so the FK in stage_preferences can resolve.
    conn.execute("CREATE TABLE projects (project_id TEXT PRIMARY KEY)")
    conn.execute("INSERT INTO projects(project_id) VALUES ('proj_001')")
    conn.executescript(_stage_migration_path().read_text(encoding="utf-8"))
    return conn


def _base_payload(**overrides: Any) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "preference_id": "pref_001",
        "scope": "project",
        "stage": None,
        "key": "narrative.tone",
        "value": "formal",
        "source": "user_explicit",
        "applies_to_artifacts": ["polished_script.json"],
        "evidence_segment_id": None,
        "created_at": "2026-04-20T00:00:00Z",
        "expires_at": None,
    }
    payload.update(overrides)
    return payload


class TestAC1StagePreferenceSchema:
    """AC-1: StagePreference scope enum + stage-presence validation."""

    def test_stage_preference_scope_enum_and_priority_validation(self) -> None:
        from src.shared.schemas.stage_preference import StagePreference

        # Valid: scope=stage requires `stage` field present.
        model = StagePreference(
            **_base_payload(
                scope="stage", stage="P5_bgm", key="bgm.target_db", value=-18
            )
        )
        assert model.scope == "stage"
        assert model.stage == "P5_bgm"

        # Invalid scope literal is rejected.
        with pytest.raises(ValidationError):
            StagePreference(**_base_payload(scope="user"))

        # scope=stage WITHOUT `stage` must fail (priority-chain invariant).
        with pytest.raises(ValidationError):
            StagePreference(**_base_payload(scope="stage", stage=None))

        # scope=global WITH `stage` set must fail (cross-scope pollution).
        with pytest.raises(ValidationError):
            StagePreference(**_base_payload(scope="global", stage="P5_bgm"))

        # All 10 stage values are accepted when scope=stage.
        for st in STAGE_VALUES:
            StagePreference(
                **_base_payload(scope="stage", stage=st, key=f"{st}.k", value=1)
            )


class TestAC2InjectionMatrix:
    """AC-2: STAGE_INJECTION_MATRIX defines P4..P9 key prefixes."""

    def test_stage_injection_matrix_defines_p4_to_p9_prefixes(self) -> None:
        from src.shared.constants.stage_injection_matrix import (
            STAGE_INJECTION_MATRIX,
        )

        required = {
            "P4_tts": "tts.*",
            "P5_bgm": "bgm.*",
            "P6_sfx": "sfx.*",
            "P7_storyboard": "storyboard.*",
            "P8_keyframe": "chart.*",
            "P9_broll": "broll.*",
        }
        for phase, prefix in required.items():
            assert phase in STAGE_INJECTION_MATRIX, (
                f"{phase} missing from STAGE_INJECTION_MATRIX "
                f"(have {sorted(STAGE_INJECTION_MATRIX)})"
            )
            patterns = STAGE_INJECTION_MATRIX[phase]
            assert prefix in patterns, (
                f"{phase} must accept '{prefix}' prefix (got {patterns})"
            )

        # visual.* is shared by P7 storyboard and P8 keyframe per spec.
        assert "visual.*" in STAGE_INJECTION_MATRIX["P7_storyboard"]
        assert "visual.*" in STAGE_INJECTION_MATRIX["P8_keyframe"]


class TestAC3MigrationCreatesStagePreferences:
    """AC-3: DDL creates stage_preferences with UNIQUE(project_id, stage, key)."""

    def test_migration_creates_stage_preferences_unique_constraint(self) -> None:
        conn = _apply_migration()

        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        }
        assert "stage_preferences" in tables, (
            f"stage_preferences table missing (got {tables})"
        )

        # UNIQUE(project_id, stage, key): a second INSERT with identical
        # triple must fail.
        params = (
            "pref_a",
            "proj_001",
            "stage",
            "P5_bgm",
            "bgm.target_db",
            "-18",
            "user_explicit",
            "[]",
            None,
            "2026-04-20T00:00:00Z",
            None,
        )
        conn.execute(
            "INSERT INTO stage_preferences "
            "(preference_id, project_id, scope, stage, key, value, source, "
            " applies_to_artifacts, evidence_segment_id, created_at, expires_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            params,
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO stage_preferences "
                "(preference_id, project_id, scope, stage, key, value, source, "
                " applies_to_artifacts, evidence_segment_id, created_at, expires_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                ("pref_b",) + params[1:],
            )


class TestAC4PriorityChain:
    """AC-4: stage > project > cross_project > global priority resolution.

    (Spec prose §A-BDD-2 lists ``user`` between cross_project and global;
    in v3.16 the scope enum collapses legacy ``user`` into ``cross_project``
    — there are 4 scopes, and cross_project carries the v3.15 user tier.)
    """

    def test_priority_chain_stage_over_project_over_cross_project_over_user_over_global(
        self,
    ) -> None:
        from src.shared.schemas.stage_preference import (
            StagePreference,
            resolve_preference,
        )

        key = "narrative.tone"
        prefs = [
            StagePreference(
                **_base_payload(
                    preference_id="pref_g",
                    scope="global",
                    stage=None,
                    key=key,
                    value="neutral",
                )
            ),
            StagePreference(
                **_base_payload(
                    preference_id="pref_x",
                    scope="cross_project",
                    stage=None,
                    key=key,
                    value="warm",
                )
            ),
            StagePreference(
                **_base_payload(
                    preference_id="pref_p",
                    scope="project",
                    stage=None,
                    key=key,
                    value="formal",
                )
            ),
            StagePreference(
                **_base_payload(
                    preference_id="pref_s",
                    scope="stage",
                    stage="P3_polish",
                    key=key,
                    value="concise",
                )
            ),
        ]

        # Highest tier wins when all present.
        winner = resolve_preference(prefs, key=key, stage="P3_polish")
        assert winner is not None and winner.preference_id == "pref_s"

        # Drop stage -> project wins.
        winner = resolve_preference(
            [p for p in prefs if p.scope != "stage"], key=key, stage="P3_polish"
        )
        assert winner is not None and winner.preference_id == "pref_p"

        # Drop project -> cross_project wins.
        winner = resolve_preference(
            [p for p in prefs if p.scope not in ("stage", "project")],
            key=key,
            stage="P3_polish",
        )
        assert winner is not None and winner.preference_id == "pref_x"

        # Only global remains.
        winner = resolve_preference(
            [p for p in prefs if p.scope == "global"], key=key, stage="P3_polish"
        )
        assert winner is not None and winner.preference_id == "pref_g"

        # Stage-scoped pref for a DIFFERENT stage must not win over project.
        mixed = [p for p in prefs if p.preference_id in ("pref_p", "pref_s")]
        winner = resolve_preference(mixed, key=key, stage="P4_tts")
        assert winner is not None and winner.preference_id == "pref_p", (
            "stage=P3_polish pref must not leak into P4_tts resolution"
        )


class TestAC5CrossStageInjectionIsolation:
    """AC-5: P5 bgm preference must NOT be injected into P4 tts."""

    def test_stage_p5_bgm_not_injected_into_p4_tts(self) -> None:
        from src.shared.constants.stage_injection_matrix import (
            STAGE_INJECTION_MATRIX,
            stage_accepts_key,
        )

        # bgm.* is declared for P5_bgm, not P4_tts.
        assert "bgm.*" in STAGE_INJECTION_MATRIX["P5_bgm"]
        assert "bgm.*" not in STAGE_INJECTION_MATRIX["P4_tts"]

        # Helper: a concrete bgm key is accepted by P5 and rejected by P4.
        assert stage_accepts_key("P5_bgm", "bgm.target_db") is True
        assert stage_accepts_key("P4_tts", "bgm.target_db") is False

        # Symmetric: tts.* keys are not injected into P5_bgm.
        assert stage_accepts_key("P4_tts", "tts.rate_multiplier") is True
        assert stage_accepts_key("P5_bgm", "tts.rate_multiplier") is False


class TestTsMirror:
    """Sanity: TS interface file mirrors the pydantic field set."""

    def test_ts_interface_matches_pydantic_fields(self) -> None:
        from src.shared.schemas.stage_preference import StagePreference

        assert TS_PATH.exists(), f"missing TS file: {TS_PATH}"
        src = TS_PATH.read_text(encoding="utf-8")

        m = re.search(r"export interface StagePreference\s*\{([^{}]+)\}", src)
        assert m, "StagePreference interface not found in stage_preference.ts"
        ts_fields = set(re.findall(r"^\s*(\w+)\??:", m.group(1), flags=re.M))
        py_fields = set(StagePreference.model_fields.keys())
        assert ts_fields == py_fields, (
            f"StagePreference field mismatch — "
            f"ts-only={ts_fields - py_fields}, py-only={py_fields - ts_fields}"
        )
