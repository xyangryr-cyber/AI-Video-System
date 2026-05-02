"""[SPEC-C-019] SFX domain exceptions.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-4.

``LayoutNotConfirmedError`` enforces the hard pre-condition that
``FinalAudioAssembler.assemble`` refuses to run until the user has
confirmed the global SFX layout plan (``user_confirmed_layout = true``).

``InvalidBaseMasterError`` guards ``SfxSegmentMixService.mix_segment``
against base_masters that are not one of the upstream masters the v3.17
P6 pipeline is allowed to derive from (narration_master or
bgm_mix_master; the no_bgm fallback path keeps narration_master).
"""

from __future__ import annotations


class LayoutNotConfirmedError(RuntimeError):
    """Raised when assemble() runs before the user confirms the layout plan."""


class InvalidBaseMasterError(ValueError):
    """Raised when mix_segment() receives a base_master whose kind is
    neither ``narration_master`` nor ``bgm_mix_master``."""


__all__ = ["InvalidBaseMasterError", "LayoutNotConfirmedError"]
