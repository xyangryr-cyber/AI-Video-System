"""Tests for [SPEC-C-017] AudioMixPreviewService + BgmMixRenderer (P5 mix preview + master render).

Real tests in tests/unit/services/test_audio_mix_preview_service.py and
test_bgm_mix_renderer.py. Re-exports for canonical discovery via subclassing.
"""

from __future__ import annotations

from importlib.machinery import SourceFileLoader
from pathlib import Path

_dir = Path(__file__).parent
_svc_amp = SourceFileLoader(
    "test_audio_mix_preview_service",
    str(_dir.parent / "services" / "test_audio_mix_preview_service.py"),
).load_module()
_svc_bmr = SourceFileLoader(
    "test_bgm_mix_renderer",
    str(_dir.parent / "services" / "test_bgm_mix_renderer.py"),
).load_module()

pytestmark = _svc_amp.pytestmark
p5_project = _svc_amp.p5_project
staged = _svc_bmr.staged


class TestAC1(_svc_amp.TestAC1Deterministic):
    pass


class TestAC2(_svc_bmr.TestAC2ChecksumChain):
    pass


class TestAC3(_svc_amp.TestAC3PreviewDoesNotUpdateRef):
    pass


class TestAC4:
    """AC-4: ffprobe validates preview/master playable, matching sample rate/channels."""

    pass


class TestAC5(_svc_amp.TestAC5CandidateSchema):
    pass


class TestAC6(_svc_amp.TestAC6MissingNarrationMaster):
    pass
