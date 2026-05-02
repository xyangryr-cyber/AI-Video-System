-- [SPEC-A-102] V004: projects.latest_reached_phase + projects.phase_history.
-- Authority: docs/specs/SPEC-A-contracts.md §A-BDD-3 (SPEC-0A.3 扩字段).
--
-- Adds two columns to the v1-core `projects` table (001_initial.sql):
--   latest_reached_phase  INTEGER  monotonic high-water mark (>= current_phase).
--   phase_history         TEXT     JSON array of PhaseHistoryEntry rows.
--
-- Legacy rows: the DEFAULT 0 from ADD COLUMN is then overwritten by an
-- UPDATE that backfills latest_reached_phase = current_phase, so existing
-- projects keep their reached level after the v3.16 upgrade (AC-1).

ALTER TABLE projects ADD COLUMN latest_reached_phase INTEGER NOT NULL DEFAULT 0;
ALTER TABLE projects ADD COLUMN phase_history TEXT NOT NULL DEFAULT '[]';

UPDATE projects SET latest_reached_phase = current_phase;
