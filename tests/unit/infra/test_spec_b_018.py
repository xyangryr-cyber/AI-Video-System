"""Canonical test for [SPEC-B-018] Real Integration Dev Environment.

Delegation shim: wraps the plain-function tests from the task card's
allowed_files module ``tests/unit/infra/test_seed_dev_db.py``
(AC-2) so the task-card verification command
``pytest tests/unit/infra/test_spec_b_018.py`` exercises the real
assertions (B-012/B-015/B-016 precedent).

Other ACs (AC-1/AC-3/AC-4/AC-5) require docker-compose / Makefile /
CI infrastructure and are exercised via integration/e2e workflows
rather than this unit-test module.
"""

from __future__ import annotations

from tests.unit.infra.test_seed_dev_db import db_path as _db_path  # noqa: F401


class TestAC2SeedsTwelvePhases:
    """AC-2: seed_dev_db inserts >=12 demo projects covering P0..P11."""

    def test_seeds_twelve_phases(self, _db_path):  # noqa: F811
        from tests.unit.infra.test_seed_dev_db import test_seeds_twelve_phases

        test_seeds_twelve_phases(_db_path)


class TestAC2SeedsIdempotent:
    """AC-2: seed_dev_db is idempotent (second run produces same rows)."""

    def test_seeds_idempotent(self, _db_path):  # noqa: F811
        from tests.unit.infra.test_seed_dev_db import test_seeds_idempotent

        test_seeds_idempotent(_db_path)
