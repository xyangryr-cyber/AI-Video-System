"""[SPEC-A-101] STAGE_INJECTION_MATRIX -- per-phase preference key patterns.

Authority: docs/specs/SPEC-A-contracts.md §A-BDD-2 (SPEC-0A.9).

Maps each runtime phase (P4..P9) to the glob-prefix set of preference
keys that are allowed to be injected into that phase. The matrix is the
enforcement point for the "aPreference extracted in phase X MUST NOT be
injected into phase Y" invariant tested by AC-5.

Global-scoped preferences (e.g. ``narrative.*``) are applied to all
phases by the resolver and are intentionally NOT listed here -- this
matrix only covers stage-scoped injection.
"""

from __future__ import annotations

import fnmatch
from collections.abc import Mapping
from types import MappingProxyType

_MATRIX: dict[str, tuple[str, ...]] = {
    "P4_tts": ("tts.*",),
    "P5_bgm": ("bgm.*",),
    "P6_sfx": ("sfx.*",),
    "P7_storyboard": ("storyboard.*", "visual.*"),
    "P8_keyframe": ("chart.*", "visual.*"),
    "P9_broll": ("broll.*",),
}

STAGE_INJECTION_MATRIX: Mapping[str, tuple[str, ...]] = MappingProxyType(_MATRIX)


def stage_accepts_key(stage: str, key: str) -> bool:
    """Return True iff ``key`` is injectable into ``stage`` under the matrix.

    Unknown stages return False (no injection). Unknown keys match only
    when the stage's pattern tuple explicitly admits them.
    """
    patterns = STAGE_INJECTION_MATRIX.get(stage)
    if not patterns:
        return False
    return any(fnmatch.fnmatchcase(key, pat) for pat in patterns)


__all__ = ["STAGE_INJECTION_MATRIX", "stage_accepts_key"]
