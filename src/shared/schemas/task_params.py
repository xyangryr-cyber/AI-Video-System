"""[SPEC-A-007] task_ledger.params validation schemas per task type.

Authority: SPEC-A-contracts.md SPEC-1B (params table keyed by `type`).
Each of the 8 V1 task types has a required-field schema enforced here
before any INSERT into `task_ledger`.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Type

from pydantic import BaseModel, ConfigDict, Field


class _StrictParams(BaseModel):
    """Base: forbid unknown fields so typos fail loudly."""

    model_config = ConfigDict(extra="forbid")


class GenerateArtifactParams(_StrictParams):
    phase_name: str
    input_refs: List[str]


class RegenerateSectionParams(_StrictParams):
    phase_name: str
    section_id: str
    instruction: str


class UserRevisionParams(_StrictParams):
    phase_name: str
    revision_text: str
    target_section: Optional[str] = None


class ReviewParams(_StrictParams):
    phase_name: str
    reviewer_name: str
    artifact_path: str


class ResearchParams(_StrictParams):
    query: str
    max_sources: int = Field(ge=3, le=5)


class VerifyParams(_StrictParams):
    data_point_id: str
    claimed_value: str
    source_url: str


class CrossCheckParams(_StrictParams):
    left_ref: str
    right_ref: str
    check_fields: List[str]


class UserAnnotationParams(_StrictParams):
    frame: int
    time_sec: float
    text: str


TASK_PARAMS_REGISTRY: Dict[str, Type[_StrictParams]] = {
    "generate_artifact": GenerateArtifactParams,
    "regenerate_section": RegenerateSectionParams,
    "user_revision": UserRevisionParams,
    "review": ReviewParams,
    "research": ResearchParams,
    "verify": VerifyParams,
    "cross_check": CrossCheckParams,
    "user_annotation": UserAnnotationParams,
}


def validate_task_params(task_type: str, payload: Mapping[str, Any]) -> _StrictParams:
    """Return the Pydantic model instance for `payload` under `task_type`.

    Raises:
        KeyError: when `task_type` is not one of the 8 V1 task types.
        pydantic.ValidationError: when `payload` is missing required fields
            or violates field-level constraints.
    """
    if task_type not in TASK_PARAMS_REGISTRY:
        raise KeyError(f"Unknown task_ledger.type: {task_type!r}")
    model_cls = TASK_PARAMS_REGISTRY[task_type]
    return model_cls.model_validate(payload)


__all__ = [
    "CrossCheckParams",
    "GenerateArtifactParams",
    "RegenerateSectionParams",
    "ResearchParams",
    "ReviewParams",
    "TASK_PARAMS_REGISTRY",
    "UserAnnotationParams",
    "UserRevisionParams",
    "VerifyParams",
    "validate_task_params",
]
