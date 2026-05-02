-- [SPEC-A-101] V003: stage_preferences table.
-- Authority: docs/specs/SPEC-A-contracts.md §A-BDD-2 (SPEC-0A.9).
--
-- Orthogonal to the v1-core 10-table DDL and to V002 (claims).
-- Introduces per-stage preference storage with UNIQUE(project_id, stage, key)
-- so the preference resolver can honour the system-mandated priority
-- chain (stage > project > cross_project > global) and the
-- STAGE_INJECTION_MATRIX cross-phase isolation invariant.

CREATE TABLE stage_preferences (
    preference_id        TEXT PRIMARY KEY,
    project_id           TEXT REFERENCES projects(project_id),
    scope                TEXT NOT NULL
        CHECK(scope IN ('global','cross_project','project','stage')),
    stage                TEXT
        CHECK(stage IS NULL OR stage IN (
            'P2_script','P3_polish','P4_tts','P5_bgm','P6_sfx',
            'P7_storyboard','P8_keyframe','P9_broll',
            'P10_roughcut','P11_finalize'
        )),
    key                  TEXT NOT NULL,
    value                TEXT NOT NULL,
    source               TEXT NOT NULL
        CHECK(source IN (
            'user_explicit','extracted_from_revision','extracted_from_confirmation'
        )),
    applies_to_artifacts TEXT NOT NULL DEFAULT '[]',
    evidence_segment_id  TEXT,
    created_at           TEXT NOT NULL
        DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    expires_at           TEXT,
    UNIQUE(project_id, stage, key)
);

CREATE INDEX idx_stage_preferences_project_stage
    ON stage_preferences(project_id, stage);
