"""Tests for [SPEC-A-002] Candidate & ProjectState Contracts."""

from __future__ import annotations

from tests.unit.contracts import test_candidate_project_state as ref


class TestAC1CandidateInterfaceFields:
    def test_candidate_interface_fields(self):
        ref.test_candidate_interface_fields()


class TestAC2CandidatePydanticValidation:
    def test_candidate_id_prefix_validation(self):
        ref.test_candidate_id_prefix_validation()

    def test_candidate_preview_type_enum(self):
        ref.test_candidate_preview_type_enum()

    def test_candidates_max_3(self):
        ref.test_candidates_max_3()


class TestAC3ProjectStateTsInterface:
    def test_project_state_structure(self):
        import re
        from pathlib import Path

        from src.shared.schemas.project_state import (
            ActiveTask,
            Preferences,
            ProjectInfo,
            ProjectState,
            SystemStatus,
        )

        root = Path(__file__).resolve().parents[3]
        ts_path = root / "src" / "shared" / "types" / "project_state.ts"
        ts = ts_path.read_text(encoding="utf-8")

        expected_core = {
            "project",
            "phases",
            "active_tasks",
            "preferences",
            "system_status",
        }
        declared = set(ProjectState.model_fields.keys())
        missing = expected_core - declared
        assert not missing, f"ProjectState missing core fields: {sorted(missing)}"

        assert set(ProjectInfo.model_fields.keys()) >= {
            "project_id",
            "title",
            "description",
            "current_phase",
            "status",
            "category",
            "updated_at",
        }
        assert set(ActiveTask.model_fields.keys()) == {
            "task_id",
            "type",
            "status",
            "progress",
            "agent_name",
        }
        assert set(Preferences.model_fields.keys()) == {
            "pending_candidates",
            "last_confirmed_at",
        }
        assert set(SystemStatus.model_fields.keys()) == {
            "all_critical_ok",
            "degraded_services",
        }

        assert re.search(r"\binterface\s+ProjectState\b", ts)
        for key in expected_core:
            assert re.search(rf"\b{key}\b", ts), f"project_state.ts missing key: {key}"


class TestAC4ProjectStatePydanticDocstrings:
    def test_project_state_computed_fields_documented(self):
        ref.test_project_state_computed_fields_documented()


class TestAC5PhaseStatusEnum:
    def test_phase_status_enum(self):
        ref.test_phase_status_enum()


class TestAC6ArtifactStatusEnum:
    def test_artifact_status_enum(self):
        ref.test_artifact_status_enum()
