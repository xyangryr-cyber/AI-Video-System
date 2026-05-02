"""[SPEC-A-017] PhaseId enum + phase_7a FSM sub-state.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §A-AUDP7A-5.

`PhaseId` is the cross-layer FSM phase identifier. P0..P11 are the 12
canonical phases from PRD §7.1; `phase_7a` is a v3.17-introduced sub-state
between P7 (Gate-P7 PASS) and P8 (KeyframeRender start). It is **not** a
thirteenth phase in PRD §7.1 — it is the FSM's way of representing the
P7A material-fetch/verify window.

Single source of truth:
  - `PhaseId` enum: the canonical set of FSM phase strings
  - `PHASE_DETAIL_ALLOWED_PHASES`: phases accepted by v3.16
    GET /projects/{id}/phases/{phase}/detail (phase param enum)
  - `PHASES_TABLE_PHASE_ID_ALLOWED_VALUES`: values allowed by the
    `phases.phase_id` DB column (DDL migration owned by D-021)

Keep in lockstep with `src/shared/types/phase_enum.ts`.
"""

from __future__ import annotations

from enum import Enum
from typing import Final, FrozenSet


class PhaseId(str, Enum):
    """Canonical FSM phase identifiers (12 phases + phase_7a sub-state)."""

    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"
    P5 = "P5"
    P6 = "P6"
    P7 = "P7"
    PHASE_7A = "phase_7a"
    P8 = "P8"
    P9 = "P9"
    P10 = "P10"
    P11 = "P11"


CANONICAL_PHASES: Final[tuple[PhaseId, ...]] = (
    PhaseId.P0,
    PhaseId.P1,
    PhaseId.P2,
    PhaseId.P3,
    PhaseId.P4,
    PhaseId.P5,
    PhaseId.P6,
    PhaseId.P7,
    PhaseId.P8,
    PhaseId.P9,
    PhaseId.P10,
    PhaseId.P11,
)

SUB_STATES: Final[tuple[PhaseId, ...]] = (PhaseId.PHASE_7A,)


PHASE_DETAIL_ALLOWED_PHASES: Final[FrozenSet[PhaseId]] = frozenset(
    CANONICAL_PHASES + SUB_STATES
)


PHASES_TABLE_PHASE_ID_ALLOWED_VALUES: Final[FrozenSet[str]] = frozenset(
    m.value for m in (*CANONICAL_PHASES, *SUB_STATES)
)


__all__ = [
    "CANONICAL_PHASES",
    "PHASES_TABLE_PHASE_ID_ALLOWED_VALUES",
    "PHASE_DETAIL_ALLOWED_PHASES",
    "PhaseId",
    "SUB_STATES",
]
