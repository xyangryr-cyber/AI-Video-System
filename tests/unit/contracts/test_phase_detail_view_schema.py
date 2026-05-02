"""Shared test implementations for [SPEC-A-102] PhaseDetailView (SPEC-0A.10).

Authority: docs/specs/SPEC-A-contracts.md §A-BDD-3 (SPEC-0A.10 新增).

Covers:
  - AC-2: PhaseDetailView exposes 7 blocks — artifacts, reviewer_results,
          gate_result, claim_snapshot, preference_snapshot,
          diff_with_previous_version, operation_history.
  - AC-4: `read_only` defaults to true for historical phases and is
          enforced false for the project's current_phase.

Also verifies the TS mirror file is field-parity with the pydantic model.

Re-exported by ``test_spec_a_102.py`` (A-100 / A-101 pattern).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[3]
TS_PATH = REPO_ROOT / "src" / "shared" / "types" / "phase_detail_view.ts"

# Required 7 sections per SPEC-A §A-BDD-3.
SEVEN_SECTIONS = (
    "artifacts",
    "reviewer_results",
    "gate_result",
    "claim_snapshot",
    "preference_snapshot",
    "diff_with_previous_version",
    "operation_history",
)


def _base_payload(**overrides):
    payload = {
        "project_id": "proj_001",
        "phase": 5,
        "status": "completed",
        "artifacts": [],
        "reviewer_results": [],
        "gate_result": None,
        "claim_snapshot": [],
        "preference_snapshot": [],
        "diff_with_previous_version": None,
        "operation_history": [],
        "read_only": True,
        "current_phase": 7,
    }
    payload.update(overrides)
    return payload


class TestAC2SevenSections:
    """AC-2: PhaseDetailView contains the 7 required analytical blocks."""

    def test_phase_detail_view_contains_seven_sections(self) -> None:
        from src.shared.schemas.phase_detail_view import PhaseDetailView

        fields = set(PhaseDetailView.model_fields.keys())
        for section in SEVEN_SECTIONS:
            assert section in fields, (
                f"PhaseDetailView missing required section '{section}' "
                f"(have {sorted(fields)})"
            )

        # Build a full instance with every section populated so the
        # contract is exercised end-to-end (not just introspected).
        model = PhaseDetailView(
            project_id="proj_001",
            phase=5,
            status="completed",
            artifacts=[
                {
                    "path": "bgm_plan.json",
                    "version": 2,
                    "size_bytes": 1024,
                    "updated_at": "2026-04-20T11:00:00Z",
                }
            ],
            reviewer_results=[
                {
                    "reviewer_name": "L1Programmatic",
                    "verdict": "PASS",
                    "ran_at": "2026-04-20T11:05:00Z",
                    "notes": ["ok"],
                }
            ],
            gate_result={
                "gate_name": "Gate5",
                "verdict": "PASS",
                "checks": [{"name": "bgm_db_within_range", "passed": True}],
            },
            claim_snapshot=[
                {
                    "claim_id": "claim_P2_1",
                    "verification_status": "verified",
                    "blocking_level": "none",
                }
            ],
            preference_snapshot=[
                {
                    "scope": "stage",
                    "stage": "P5_bgm",
                    "key": "bgm.target_db",
                    "value": -18,
                }
            ],
            diff_with_previous_version={
                "added": ["bgm_plan.json:v2"],
                "removed": [],
                "modified": ["bgm_plan.json"],
            },
            operation_history=[
                {
                    "ts": "2026-04-20T11:00:00Z",
                    "action": "generate_artifact",
                    "actor": "system",
                    "ref": "task_xyz",
                }
            ],
            read_only=True,
            current_phase=7,
        )
        # Sanity: each of the 7 sections survived validation.
        assert len(model.artifacts) == 1
        assert model.reviewer_results[0]["verdict"] == "PASS"
        assert model.gate_result is not None
        assert model.gate_result["gate_name"] == "Gate5"
        assert model.claim_snapshot[0]["claim_id"] == "claim_P2_1"
        assert model.preference_snapshot[0]["scope"] == "stage"
        assert model.diff_with_previous_version is not None
        assert "bgm_plan.json:v2" in model.diff_with_previous_version["added"]
        assert model.operation_history[0]["actor"] == "system"


class TestAC4ReadOnlyDefault:
    """AC-4: read_only defaults True for history, must be False when
    phase == current_phase."""

    def test_read_only_defaults_true_for_history_false_for_current_phase(self) -> None:
        from src.shared.schemas.phase_detail_view import PhaseDetailView

        # Default (omit read_only): historical phase => True.
        payload = _base_payload(phase=5, current_phase=7)
        payload.pop("read_only")
        historical = PhaseDetailView(**payload)
        assert historical.read_only is True, (
            "historical phase (phase < current_phase) must default read_only=True"
        )

        # Current phase: read_only must be False.
        current = PhaseDetailView(
            **_base_payload(phase=7, current_phase=7, read_only=False)
        )
        assert current.read_only is False

        # Invariant: read_only=True with phase == current_phase is rejected
        # (locking the editable phase is a contract violation).
        with pytest.raises(ValidationError):
            PhaseDetailView(**_base_payload(phase=7, current_phase=7, read_only=True))

        # Invariant: read_only=False on a historical phase is rejected
        # (spec §A-BDD-3: history editing requires explicit POST /revert).
        with pytest.raises(ValidationError):
            PhaseDetailView(**_base_payload(phase=5, current_phase=7, read_only=False))


class TestTsMirror:
    """TS `PhaseDetailView` interface must mirror the pydantic field set."""

    def test_ts_interface_matches_pydantic_fields(self) -> None:
        from src.shared.schemas.phase_detail_view import PhaseDetailView

        assert TS_PATH.exists(), f"missing TS file: {TS_PATH}"
        src = TS_PATH.read_text(encoding="utf-8")

        m = re.search(r"export interface PhaseDetailView\s*\{([^{}]+)\}", src)
        assert m, "PhaseDetailView interface not found in phase_detail_view.ts"
        ts_fields = set(re.findall(r"^\s*(\w+)\??:", m.group(1), flags=re.M))
        py_fields = set(PhaseDetailView.model_fields.keys())
        assert ts_fields == py_fields, (
            f"PhaseDetailView field mismatch — "
            f"ts-only={ts_fields - py_fields}, py-only={py_fields - ts_fields}"
        )
