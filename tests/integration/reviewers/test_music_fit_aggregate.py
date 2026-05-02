"""[SPEC-C-018] AC-4/AC-5/AC-6 aggregate + regression tests.

Re-exports AC-4 / AC-5 / AC-6 classes from
``tests/unit/backend-core/test_spec_c_018.py`` (dynamic import because
the ``backend-core`` folder name has a dash). Same pattern as
``tests/unit/reviewers/test_music_fit_reviewer_v317.py``.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_spec_path = (
    Path(__file__).resolve().parents[2] / "unit" / "backend-core" / "test_spec_c_018.py"
)
_spec = importlib.util.spec_from_file_location("_spec_c_018_agg_real_tests", _spec_path)
assert _spec is not None and _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

TestAC4 = _mod.TestAC4
TestAC5 = _mod.TestAC5
TestAC6 = _mod.TestAC6
