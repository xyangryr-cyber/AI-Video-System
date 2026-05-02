"""[SPEC-C-018] v3.17 independent unit tests for the 3 new L1 checks.

Re-exports the AC-1 / AC-2 / AC-3 / AC-7 test classes from
``tests/unit/backend-core/test_spec_c_018.py`` so the task-card
``allowed_files`` entry for this path also runs real assertions. The
``backend-core`` folder name is not a valid Python identifier (dash),
so we load it via :func:`importlib.util.spec_from_file_location`; same
approach a future refactor can collapse if the folder is ever renamed.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_spec_path = (
    Path(__file__).resolve().parents[2] / "unit" / "backend-core" / "test_spec_c_018.py"
)
_spec = importlib.util.spec_from_file_location("_spec_c_018_real_tests", _spec_path)
assert _spec is not None and _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

TestAC1 = _mod.TestAC1
TestAC2 = _mod.TestAC2
TestAC3 = _mod.TestAC3
TestAC7 = _mod.TestAC7
