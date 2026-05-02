"""Pydantic models for ProjectState (SPEC-0A.3).

The `GET /api/projects/{id}/state` response. Drives frontend state
restoration. Several fields are not persisted on `phases` but computed
by the API layer; those are documented in the model docstrings.
"""

from __future__ import annotations

from typing import List, Literal, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

PhaseStatus = Literal["pending", "active", "completed", "skipped", "invalidated"]
ArtifactStatus = Literal["ok", "damaged", "missing"]
ReviewStatus = Literal["pending", "passed", "failed"]
ProjectStatus = Literal["active", "completed", "archived"]

PHASE_STATUS_VALUES: Tuple[PhaseStatus, ...] = (
    "pending",
    "active",
    "completed",
    "skipped",
    "invalidated",
)

ARTIFACT_STATUS_VALUES: Tuple[Optional[str], ...] = (
    "ok",
    "damaged",
    "missing",
    None,
)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProjectInfo(_Strict):
    project_id: str = Field(min_length=1)
    title: str
    description: str
    current_phase: int = Field(ge=0, le=11)
    status: ProjectStatus
    category: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class PhaseState(_Strict):
    """Per-phase state entry in ProjectState.phases.

    Computed fields (NOT stored on the `phases` row):
      - `artifact_url`: built by the API layer from `phases.artifact_path`
        as `/api/projects/{id}/phases/{phase}/artifact`.
      - `review_status`: derived from the latest review entry in
        `task_ledger` for this phase:
          * no review task -> None
          * review task running/pending -> 'pending'
          * review task succeeded + verdict=PASS -> 'passed'
          * review task succeeded + verdict=FAIL -> 'failed'
    """

    phase_num: int = Field(ge=0, le=11)
    phase_name: str = Field(min_length=1)
    status: PhaseStatus
    artifact_version: int = Field(ge=0)
    artifact_status: Optional[ArtifactStatus]
    artifact_url: Optional[str]
    review_status: Optional[ReviewStatus]
    preferences_confirmed: bool
    style_lock_path: Optional[str]


class ActiveTask(_Strict):
    task_id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    status: str = Field(min_length=1)
    progress: int = Field(ge=0, le=100)
    agent_name: Optional[str]


class Preferences(_Strict):
    pending_candidates: int = Field(ge=0)
    last_confirmed_at: Optional[str]


class SystemStatus(_Strict):
    """Aggregated system health exposed to the frontend.

    Computed by the API layer from the `system_status` table, picking
    rows where `valid_until > NOW()`:
      - `all_critical_ok`: True iff every row with is_critical=1 has
        status='ok'.
      - `degraded_services`: check_name list for rows with status='degraded'.
    """

    all_critical_ok: bool
    degraded_services: List[str]


class MasterAudioRef(_Strict):
    """SPEC-A-013 compact pointer to the current master audio artifact.

    Mirrors the summary fields of `MasterAudioArtifact` without the chain
    detail (source_ref / derived_from_segments). Updated by the FSM when
    Gate 4/5/6 passes; `None` on projects that have not reached P4 yet.
    """

    kind: Literal["narration_master", "bgm_mix_master", "final_audio_master"]
    file_path: str = Field(min_length=1)
    based_on_phase: Literal[4, 5, 6]
    checksum: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    version: int = Field(ge=1)


class ProjectSummary(_Strict):
    """Frontend-facing project list/summary item.

    Shape returned by `GET /api/projects` (list) and `POST /api/projects`
    (create). Distinct from `ProjectInfo` because the list/dashboard UI
    exposes two computed fields (`latest_reached_phase`, `progress`) and
    uses `id` as the primary identifier. `project_id` and `description`
    are present on list items but absent on the create response, so both
    are optional here.
    """

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status: str = Field(min_length=1)
    current_phase: int = Field(ge=0, le=11)
    latest_reached_phase: int = Field(ge=0, le=11)
    progress: int = Field(ge=0, le=100)
    updated_at: str = Field(min_length=1)
    category: str = Field(min_length=1)
    description: Optional[str] = None
    project_id: Optional[str] = None


class PhaseHistoryEntry(_Strict):
    """Per-phase timeline entry (SPEC-A-102 / SPEC-0A.3 v3.16 extension).

    Emitted into ``ProjectState.phase_history`` when the FSM advances,
    completes, or records a revision on a phase. ``reached_at`` is
    mandatory (the phase was at least entered); ``completed_at`` and
    ``last_revision_at`` are set opportunistically by the engine.
    """

    phase: int = Field(ge=0, le=11)
    reached_at: str = Field(min_length=1)
    completed_at: Optional[str] = None
    last_revision_at: Optional[str] = None


class ProjectState(_Strict):
    """Full payload returned by `GET /api/projects/{id}/state`.

    Several members are computed, not stored:
      - `phases[].artifact_url` is derived from `phases.artifact_path`.
      - `phases[].review_status` is derived from `task_ledger`.
      - `system_status` is aggregated from the `system_status` table.
      - `master_audio_ref` is hydrated from `projects.master_audio_ref`
        (SPEC-A-013) and is `None` until Gate 4 passes.
      - `latest_reached_phase` is the monotonic high-water mark
        maintained by the WorkflowEngine (SPEC-A-102 / SPEC-0A.3 v3.16);
        defaults to 0 on legacy rows and is backfilled to
        ``current_phase`` by the V004 migration.
      - `phase_history` is a JSON array of ``PhaseHistoryEntry`` rows;
        empty by default on legacy projects.
    See `PhaseState` and `SystemStatus` docstrings for the exact rules.
    """

    project: ProjectInfo
    phases: List[PhaseState]
    active_tasks: List[ActiveTask]
    preferences: Preferences
    system_status: SystemStatus
    master_audio_ref: Optional[MasterAudioRef] = None
    latest_reached_phase: int = Field(default=0, ge=0, le=11)
    phase_history: List[PhaseHistoryEntry] = Field(default_factory=list)


__all__ = [
    "ARTIFACT_STATUS_VALUES",
    "PHASE_STATUS_VALUES",
    "ActiveTask",
    "ArtifactStatus",
    "MasterAudioRef",
    "PhaseHistoryEntry",
    "PhaseState",
    "PhaseStatus",
    "Preferences",
    "ProjectInfo",
    "ProjectState",
    "ProjectStatus",
    "ProjectSummary",
    "ReviewStatus",
    "SystemStatus",
]
