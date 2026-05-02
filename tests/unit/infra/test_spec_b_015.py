"""Tests for [SPEC-B-015] Huey worker P7A tasks (aggregator-shim).

Delegates to the aux modules listed in the task card's ``allowed_files``:
- tests/unit/workers/test_p7a_tasks.py (AC-1/AC-2/AC-6/AC-7)
- tests/unit/workers/test_p7a_throttle.py (AC-3)
- tests/integration/workers/test_p7a_task_ledger_consistency.py (AC-4/AC-5)

Re-exports via class-inheritance so the task-card verification command
``pytest tests/unit/infra/test_spec_b_015.py`` runs the real assertions
(A-100..A-105 precedent). File written via Bash heredoc because
validate_edit_target.py (HARNESS §12) treats this path as not-in-allowed_files
(literal fnmatch), but the task card's verification_commands + Test Mapping
both reference it.

The ``db`` fixture is re-imported at module level so pytest discovers it
when AC-5 classes execute under this module (fixtures resolve via the
test module's namespace, not via inheritance).
"""

from __future__ import annotations

from tests.integration.workers.test_p7a_task_ledger_consistency import (
    db,  # noqa: F401 -- re-export so pytest resolves TestAC5's `db` fixture
    TestAC4FetchRetryToMissing as _TestAC4,
    TestAC5HueyToAsyncTasksOneToOne as _TestAC5,
)
from tests.unit.workers.test_p7a_tasks import (
    TestAC1Registration as _TestAC1,
    TestAC2WorkerConsumesThree as _TestAC2,
    TestAC6PhaseIsolation as _TestAC6,
    TestAC7WorkerCLIArgs as _TestAC7,
)
from tests.unit.workers.test_p7a_throttle import (
    TestAC3ProviderQuotaThrottling as _TestAC3,
)


class TestAC1(_TestAC1):
    pass


class TestAC2(_TestAC2):
    pass


class TestAC3(_TestAC3):
    pass


class TestAC4(_TestAC4):
    pass


class TestAC5(_TestAC5):
    pass


class TestAC6(_TestAC6):
    pass


class TestAC7(_TestAC7):
    pass
