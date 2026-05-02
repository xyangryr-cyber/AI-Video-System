// [SPEC-A-017] PhaseId type + phase_7a FSM sub-state.
//
// Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §A-AUDP7A-5.
//
// Mirrors src/shared/schemas/phase_enum.py. P0..P11 are the 12 canonical
// phases from PRD §7.1; `phase_7a` is a v3.17-introduced FSM sub-state
// between P7 and P8 (NOT a thirteenth phase in PRD §7.1).

export type PhaseId =
  | 'P0'
  | 'P1'
  | 'P2'
  | 'P3'
  | 'P4'
  | 'P5'
  | 'P6'
  | 'P7'
  | 'phase_7a'
  | 'P8'
  | 'P9'
  | 'P10'
  | 'P11';

export const CANONICAL_PHASES: readonly PhaseId[] = [
  'P0', 'P1', 'P2', 'P3', 'P4', 'P5',
  'P6', 'P7', 'P8', 'P9', 'P10', 'P11',
] as const;

export const SUB_STATES: readonly PhaseId[] = ['phase_7a'] as const;

// Phases accepted by v3.16 GET /projects/{id}/phases/{phase}/detail.
export const PHASE_DETAIL_ALLOWED_PHASES: readonly PhaseId[] = [
  'P0', 'P1', 'P2', 'P3', 'P4', 'P5',
  'P6', 'P7', 'phase_7a', 'P8', 'P9', 'P10', 'P11',
] as const;

// Values allowed by the phases.phase_id DB column (DDL owned by D-021).
export const PHASES_TABLE_PHASE_ID_ALLOWED_VALUES: readonly PhaseId[] = [
  'P0', 'P1', 'P2', 'P3', 'P4', 'P5',
  'P6', 'P7', 'phase_7a', 'P8', 'P9', 'P10', 'P11',
] as const;
