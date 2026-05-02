-- [SPEC-B-013] V006: projects.master_audio_ref + expression index.
-- Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §B-AUDP7A-1.
-- Depends on SPEC-A-013 `MasterAudioRef` schema
-- (src/shared/schemas/project_state.py).
--
-- SPEC-1B ownership hint (for the docs PR tracked by AC-6):
--   Table:        projects
--   Column:       master_audio_ref  TEXT (nullable, JSON)
--   Writers:      NarrationMasterAssembler (based_on_phase=4),
--                 BgmMixRenderer           (based_on_phase=5),
--                 FinalAudioAssembler      (based_on_phase=6).
--   Write timing: Gate 4 PASS / Gate 5 PASS / Gate 6 PASS respectively.
--   Readers:      frontend 主播放器 (GET /projects/{id}/artifacts/master_audio),
--                 P7-P11 主音频消费者 (downstream FSM phases that rely on
--                 the latest master audio chain).
--
-- SQLite 3.35+ supports ALTER TABLE ... DROP COLUMN, so rollback avoids the
-- 12-step table rebuild. The expression index on
-- json_extract(master_audio_ref, '$.based_on_phase') accelerates the
-- frontend `?phase=4|5|6` lookup without materialising another column.

-- Forward ------------------------------------------------------------------

ALTER TABLE projects ADD COLUMN master_audio_ref TEXT;

CREATE INDEX idx_projects_master_audio_phase
    ON projects(json_extract(master_audio_ref, '$.based_on_phase'));

-- ROLLBACK -----------------------------------------------------------------
-- Split by the test harness at this marker (see
-- scripts/migrations/test_migration_master_audio_ref.py::_split_forward_rollback).

DROP INDEX IF EXISTS idx_projects_master_audio_phase;

ALTER TABLE projects DROP COLUMN master_audio_ref;
