"""Tests for [SPEC-C-016] NarrationMasterAssembler (P4 main audio assembly).

Real tests in tests/unit/services/test_narration_master_assembler.py.
Re-exports for canonical test discovery via subclassing.
"""

from __future__ import annotations

from importlib.machinery import SourceFileLoader
from pathlib import Path

_dir = Path(__file__).parent
_svc_nma = SourceFileLoader(
    "test_narration_master_assembler",
    str(_dir.parent / "services" / "test_narration_master_assembler.py"),
).load_module()

pytestmark = _svc_nma.pytestmark
three_segment_project = _svc_nma.three_segment_project


class TestAC1(_svc_nma.TestAC1LosslessConcat):
    pass


class TestAC2(_svc_nma.TestAC2MissingSegment):
    pass


class TestAC3(_svc_nma.TestAC3ChecksumStable):
    pass


class TestAC4(_svc_nma.TestAC4MasterAudioRefPersisted):
    pass


class TestAC5(_svc_nma.TestAC5TransactionalRollback):
    pass


class TestAC6(_svc_nma.TestAC6Metadata):
    pass
