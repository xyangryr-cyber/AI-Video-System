"""Tests for [SPEC-A-002] Candidate & ProjectState Contracts.

Covers AC-1..AC-6 from tasks/SPEC-A/A-002-candidate-and-project-state.md
against SPEC-0A.2 (Candidate) and SPEC-0A.3 (ProjectState).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.shared.schemas.candidate import (
    PREVIEW_TYPES,
    Candidate,
    CandidateList,
)
from src.shared.schemas.project_state import (
    ARTIFACT_STATUS_VALUES,
    PHASE_STATUS_VALUES,
    ActiveTask,
    PhaseState,
    Preferences,
    ProjectInfo,
    ProjectState,
    SystemStatus,
)

ROOT = Path(__file__).resolve().parents[3]
TS_CANDIDATE = ROOT / "src" / "shared" / "types" / "candidate.ts"
TS_PROJECT_STATE = ROOT / "src" / "shared" / "types" / "project_state.ts"


def _valid_candidate(**overrides) -> dict:
    base = {
        "candidate_id": "cand_abc123",
        "preview_url": "https://example.com/preview.mp3",
        "preview_type": "audio",
        "style_tags": ["warm", "calm"],
        "description": "Warm calm female narration",
        "is_recommended": True,
        "adjustable_params": {"rate_wpm": 280},
        "rationale": "Matches requested tone",
    }
    base.update(overrides)
    return base


def _minimal_phase(**overrides) -> dict:
    base = {
        "phase_num": 3,
        "phase_name": "script",
        "status": "pending",
        "artifact_version": 0,
        "artifact_status": None,
        "artifact_url": None,
        "review_status": None,
        "preferences_confirmed": False,
        "style_lock_path": None,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# AC-1: Candidate interface has all 8 fields
# ---------------------------------------------------------------------------
def test_candidate_interface_fields():
    expected = {
        "candidate_id",
        "preview_url",
        "preview_type",
        "style_tags",
        "description",
        "is_recommended",
        "adjustable_params",
        "rationale",
        "raw_bgm_url",
    }
    assert set(Candidate.model_fields.keys()) == expected
    ts = TS_CANDIDATE.read_text(encoding="utf-8")
    assert re.search(r"\binterface\s+Candidate\b", ts), (
        "candidate.ts must declare Candidate interface"
    )
    for field in expected:
        assert re.search(rf"\b{field}\b", ts), f"candidate.ts missing field: {field}"


# ---------------------------------------------------------------------------
# AC-2: Pydantic validation rules
# ---------------------------------------------------------------------------
def test_candidate_id_prefix_validation():
    Candidate.model_validate(_valid_candidate())
    with pytest.raises(ValidationError):
        Candidate.model_validate(_valid_candidate(candidate_id="bad_123"))
    with pytest.raises(ValidationError):
        Candidate.model_validate(_valid_candidate(candidate_id="cand"))


def test_candidate_preview_type_enum():
    assert set(PREVIEW_TYPES) == {"audio", "image", "video", "color_palette"}
    for value in PREVIEW_TYPES:
        Candidate.model_validate(_valid_candidate(preview_type=value))
    with pytest.raises(ValidationError):
        Candidate.model_validate(_valid_candidate(preview_type="text"))


def test_candidates_max_3():
    three = [_valid_candidate(candidate_id=f"cand_{i:03d}") for i in range(3)]
    CandidateList.model_validate({"candidates": three})

    four = [_valid_candidate(candidate_id=f"cand_{i:03d}") for i in range(4)]
    with pytest.raises(ValidationError):
        CandidateList.model_validate({"candidates": four})


# ---------------------------------------------------------------------------
# AC-3: ProjectState top-level shape
# ---------------------------------------------------------------------------
def test_project_state_structure():
    # AC-3 baseline: the 5 core SPEC-0A.3 fields must be present. SPEC-A-013
    # added `master_audio_ref` as an optional extension; later SPEC-A cards
    # may add similarly-optional pointers. Enforce the core set as a
    # superset invariant rather than strict equality.
    core_fields = {
        "project",
        "phases",
        "active_tasks",
        "preferences",
        "system_status",
    }
    field_keys = set(ProjectState.model_fields.keys())
    missing = core_fields - field_keys
    assert not missing, f"ProjectState dropped core fields: {missing}"
    assert set(ProjectInfo.model_fields.keys()) == {
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

    ts = TS_PROJECT_STATE.read_text(encoding="utf-8")
    assert re.search(r"\binterface\s+ProjectState\b", ts)
    for key in ("project", "phases", "active_tasks", "preferences", "system_status"):
        assert re.search(rf"\b{key}\b", ts), f"project_state.ts missing key: {key}"


# ---------------------------------------------------------------------------
# AC-4: Computed field docstrings
# ---------------------------------------------------------------------------
def test_project_state_computed_fields_documented():
    corpus = "\n".join(
        filter(
            None,
            [
                ProjectState.__doc__,
                PhaseState.__doc__,
                SystemStatus.__doc__,
            ],
        )
    )
    for marker in (
        "review_status",
        "task_ledger",
        "artifact_url",
        "artifact_path",
        "system_status",
    ):
        assert marker in corpus, f"missing docstring marker: {marker}"


# ---------------------------------------------------------------------------
# AC-5: Phase status enum
# ---------------------------------------------------------------------------
def test_phase_status_enum():
    assert set(PHASE_STATUS_VALUES) == {
        "pending",
        "active",
        "completed",
        "skipped",
        "invalidated",
    }
    for value in PHASE_STATUS_VALUES:
        PhaseState.model_validate(_minimal_phase(status=value))
    with pytest.raises(ValidationError):
        PhaseState.model_validate(_minimal_phase(status="done"))


# ---------------------------------------------------------------------------
# AC-6: Artifact status enum (nullable)
# ---------------------------------------------------------------------------
def test_artifact_status_enum():
    assert set(ARTIFACT_STATUS_VALUES) == {"ok", "damaged", "missing", None}
    for value in ("ok", "damaged", "missing", None):
        PhaseState.model_validate(_minimal_phase(artifact_status=value))
    with pytest.raises(ValidationError):
        PhaseState.model_validate(_minimal_phase(artifact_status="corrupt"))
