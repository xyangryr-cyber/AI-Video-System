"""[SPEC-A-013] MasterAudioArtifact schema (Pydantic).

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md A-AUDP7A-1.

`MasterAudioArtifact` is a discriminated union (by `kind`) over three
concrete master-audio artifacts: narration_master (P4), bgm_mix_master
(P5), final_audio_master (P6). Keep in lockstep with
`schemas/audio_master.schema.json` and `src/shared/types/audio_master.ts`.
"""

from __future__ import annotations

from typing import Annotated, List, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


_CHECKSUM_RE = r"^sha256:[a-f0-9]{64}$"
_SEGMENT_ID_RE = r"^seg_\d{2,}$"
_FILE_PATH_RE = r"^phase_[456a]/.+\.(mp3|wav)$"


class SourceRef(_Strict):
    """Back-reference to the upstream master whose checksum must be reproduced."""

    kind: Literal["narration_master", "bgm_mix_master"]
    checksum: str = Field(pattern=_CHECKSUM_RE)


class _MasterAudioCommon(_Strict):
    file_path: str = Field(pattern=_FILE_PATH_RE)
    based_on_phase: Literal[4, 5, 6]
    derived_from_segments: List[str] = Field(
        default_factory=list,
        description="Segment IDs composing this master (each matches ^seg_\\d{2,}$).",
    )
    total_duration_seconds: float = Field(ge=0)
    checksum: str = Field(pattern=_CHECKSUM_RE)
    version: int = Field(ge=1)


def _validate_segment_ids(segments: List[str]) -> None:
    import re

    pat = re.compile(_SEGMENT_ID_RE)
    for seg_id in segments:
        if not pat.match(seg_id):
            raise ValueError(
                f"derived_from_segments contains invalid id {seg_id!r} "
                f"(expected pattern {_SEGMENT_ID_RE})"
            )


class NarrationMasterArtifact(_MasterAudioCommon):
    """P4 narration master (no source_ref -- it is the chain root)."""

    kind: Literal["narration_master"]

    def model_post_init(self, __context: object) -> None:
        _validate_segment_ids(self.derived_from_segments)


class BgmMixMasterArtifact(_MasterAudioCommon):
    """P5 BGM mix master (source_ref pins the upstream narration checksum)."""

    kind: Literal["bgm_mix_master"]
    source_ref: SourceRef

    def model_post_init(self, __context: object) -> None:
        _validate_segment_ids(self.derived_from_segments)


class FinalAudioMasterArtifact(_MasterAudioCommon):
    """P6 final audio master (source_ref pins the upstream BGM-mix checksum)."""

    kind: Literal["final_audio_master"]
    source_ref: SourceRef

    def model_post_init(self, __context: object) -> None:
        _validate_segment_ids(self.derived_from_segments)


MasterAudioArtifact = Annotated[
    Union[
        NarrationMasterArtifact,
        BgmMixMasterArtifact,
        FinalAudioMasterArtifact,
    ],
    Field(discriminator="kind"),
]

MasterAudioArtifactAdapter: TypeAdapter[MasterAudioArtifact] = TypeAdapter(
    MasterAudioArtifact
)


def validate_checksum_chain(
    child: MasterAudioArtifact,
    parent: MasterAudioArtifact,
) -> None:
    """Enforce the A-AUDP7A-1 checksum chain invariant.

    - `bgm_mix_master.source_ref.checksum` MUST equal `narration_master.checksum`.
    - `final_audio_master.source_ref.checksum` MUST equal `bgm_mix_master.checksum`.

    Raises ValueError if the chain is broken or if the kinds do not form a
    legal (parent, child) pair.
    """
    expected_parent_by_child: dict[str, str] = {
        "bgm_mix_master": "narration_master",
        "final_audio_master": "bgm_mix_master",
    }
    child_kind = child.kind
    if child_kind not in expected_parent_by_child:
        raise ValueError(
            f"validate_checksum_chain only applies to chained children "
            f"(bgm_mix_master, final_audio_master); got kind={child_kind!r}"
        )
    expected_parent_kind = expected_parent_by_child[child_kind]
    if parent.kind != expected_parent_kind:
        raise ValueError(
            f"checksum chain mismatch: {child_kind} requires parent of kind "
            f"{expected_parent_kind!r}, got parent kind={parent.kind!r}"
        )
    source_ref = getattr(child, "source_ref", None)
    if source_ref is None:
        raise ValueError(f"checksum chain broken: {child_kind} is missing source_ref")
    if source_ref.kind != parent.kind:
        raise ValueError(
            f"checksum chain broken: source_ref.kind={source_ref.kind!r} "
            f"does not match parent kind={parent.kind!r}"
        )
    if source_ref.checksum != parent.checksum:
        raise ValueError(
            f"checksum chain broken: source_ref.checksum={source_ref.checksum!r} "
            f"!= parent.checksum={parent.checksum!r}"
        )


__all__ = [
    "BgmMixMasterArtifact",
    "FinalAudioMasterArtifact",
    "MasterAudioArtifact",
    "MasterAudioArtifactAdapter",
    "NarrationMasterArtifact",
    "SourceRef",
    "validate_checksum_chain",
]
