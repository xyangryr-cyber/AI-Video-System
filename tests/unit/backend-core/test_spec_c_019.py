"""Tests for [SPEC-C-019] SfxSegmentMixService + FinalAudioAssembler (P6 dual-layer + final master).

Real tests in tests/unit/services/test_sfx_segment_mix_service.py and
test_final_audio_assembler.py. Re-exports for canonical discovery via subclassing.
"""

from __future__ import annotations

from importlib.machinery import SourceFileLoader
from pathlib import Path

_dir = Path(__file__).parent
_svc_ssm = SourceFileLoader(
    "test_sfx_segment_mix_service",
    str(_dir.parent / "services" / "test_sfx_segment_mix_service.py"),
).load_module()
_svc_faa = SourceFileLoader(
    "test_final_audio_assembler",
    str(_dir.parent / "services" / "test_final_audio_assembler.py"),
).load_module()

pytestmark = _svc_ssm.pytestmark
staged = _svc_ssm.staged
prepared_segments = _svc_faa.prepared_segments


class TestAC1(_svc_ssm.TestAC1TriggerEnergyInWindow):
    pass


class TestAC2(_svc_faa.TestAC2AssembleTotalDurationAndChain):
    pass


class TestAC3(_svc_faa.TestAC3LayoutNotConfirmed):
    pass


class TestAC4(_svc_ssm.TestAC4SfxMixSegmentsJsonConsistentWithFs):
    pass


class TestAC5(_svc_ssm.TestAC5SingleSegmentRemixIsolation):
    pass


class TestAC6(_svc_faa.TestAC6MasterAudioRefFinalKind):
    pass


class TestAC7(_svc_ssm.TestAC7InvalidBaseMaster):
    pass
