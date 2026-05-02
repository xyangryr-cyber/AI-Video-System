"""Tests for [SPEC-A-017] PhaseId enum (FSM phase枚举 + phase_7a 子态).

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md A-AUDP7A-5.

Covers AC-4 (PhaseId 新增 phase_7a，既有 P0-P11 不删不改),
AC-5 (v3.16 GET /phases/{phase}/detail 枚举扩展),
AC-6 (phases 表 phase_id 列允许 phase_7a 值 — 契约层文档化).
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TS_PHASE_ENUM_PATH = ROOT / "src" / "shared" / "types" / "phase_enum.ts"


CANONICAL_P0_TO_P11 = (
    "P0",
    "P1",
    "P2",
    "P3",
    "P4",
    "P5",
    "P6",
    "P7",
    "P8",
    "P9",
    "P10",
    "P11",
)
SUBSTATES = ("phase_7a",)


class TestAC4PhaseIdEnum:
    """AC-4: PhaseId 新增 phase_7a；P0-P11 不删不改；TS + Pydantic 同步."""

    def test_phase_7a_in_enum(self):
        from src.shared.schemas.phase_enum import PhaseId

        assert "phase_7a" in {m.value for m in PhaseId}, (
            "PhaseId must contain 'phase_7a' sub-state"
        )

    def test_p0_to_p11_unchanged(self):
        from src.shared.schemas.phase_enum import PhaseId

        values = {m.value for m in PhaseId}
        for canonical in CANONICAL_P0_TO_P11:
            assert canonical in values, f"PhaseId lost canonical value {canonical!r}"

        # Size check: exactly 12 canonical + 1 sub-state
        assert len(values) == len(CANONICAL_P0_TO_P11) + len(SUBSTATES), (
            f"PhaseId unexpectedly has {len(values)} members; "
            f"expected {len(CANONICAL_P0_TO_P11) + len(SUBSTATES)}"
        )

    def test_ts_pydantic_parity(self):
        from src.shared.schemas.phase_enum import PhaseId

        ts_src = TS_PHASE_ENUM_PATH.read_text(encoding="utf-8")
        for member in PhaseId:
            quoted = f"'{member.value}'"
            assert quoted in ts_src or f'"{member.value}"' in ts_src, (
                f"TS phase_enum.ts missing PhaseId member {member.value!r}"
            )


class TestAC5PhaseDetailSupportsPhase7a:
    """AC-5: v3.16 GET /phases/{phase}/detail 接受 phase_7a（回归测试 v3.16 既有路径）."""

    def test_v316_phase_detail_supports_phase_7a(self):
        from src.shared.schemas.phase_enum import (
            PHASE_DETAIL_ALLOWED_PHASES,
            PhaseId,
        )

        assert PhaseId.PHASE_7A in PHASE_DETAIL_ALLOWED_PHASES, (
            "GET /phases/{phase}/detail must accept phase_7a (v3.17 A-AUDP7A-5 AC-5)"
        )

    def test_v316_phase_detail_retains_p0_to_p11(self):
        from src.shared.schemas.phase_enum import (
            PHASE_DETAIL_ALLOWED_PHASES,
            PhaseId,
        )

        for canonical in CANONICAL_P0_TO_P11:
            assert PhaseId(canonical) in PHASE_DETAIL_ALLOWED_PHASES, (
                f"v3.16 regression: GET /phases/{{phase}}/detail dropped {canonical}"
            )


class TestAC6PhasesTableColumnAllowsPhase7a:
    """AC-6: phases 表 phase_id 列允许 phase_7a 值（契约层文档化）.

    DDL 由 D-021 承担；此处仅在 schema 层发布可写入集合的单一事实源，
    使 C-021 / D-021 实现 DDL 迁移时有唯一常量可 import.
    """

    def test_phase_id_column_allows_phase_7a_value(self):
        from src.shared.schemas.phase_enum import (
            PHASES_TABLE_PHASE_ID_ALLOWED_VALUES,
        )

        assert "phase_7a" in PHASES_TABLE_PHASE_ID_ALLOWED_VALUES, (
            "phases.phase_id column contract must allow 'phase_7a' "
            "(A-AUDP7A-5 §AC-6; DDL migration owned by D-021)"
        )

    def test_phase_id_column_retains_p0_to_p11(self):
        from src.shared.schemas.phase_enum import (
            PHASES_TABLE_PHASE_ID_ALLOWED_VALUES,
        )

        for canonical in CANONICAL_P0_TO_P11:
            assert canonical in PHASES_TABLE_PHASE_ID_ALLOWED_VALUES, (
                f"phases.phase_id column contract dropped {canonical}; v3.16 regression"
            )

    def test_ts_exports_column_contract(self):
        """TS mirror must export the same allowed-values list so frontend
        validation and backend DDL agree at compile time."""
        ts_src = TS_PHASE_ENUM_PATH.read_text(encoding="utf-8")
        # The allowed-values array must at minimum mention every canonical
        # value and 'phase_7a' so a future codegen / eslint rule can assert
        # parity against the Python side.
        for value in list(CANONICAL_P0_TO_P11) + list(SUBSTATES):
            assert re.search(rf"['\"]{re.escape(value)}['\"]", ts_src), (
                f"TS phase_enum.ts must reference {value!r} "
                f"(required for PHASES_TABLE_PHASE_ID_ALLOWED_VALUES parity)"
            )
