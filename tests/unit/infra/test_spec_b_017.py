"""Canonical test for [SPEC-B-017] Frontend Mock Layer + Fixture Single Source.

Delegation shim: wraps the plain-function tests from the task card's
allowed_files module ``tests/unit/infra/test_validate_fixtures.py``
(AC-3) so the task-card verification command
``pytest tests/unit/infra/test_spec_b_017.py`` exercises the real
assertions (B-012/B-015/B-016 precedent).

Other ACs (AC-1/AC-2/AC-5) live in the frontend vitest suite
(``tests/unit/frontend/mocks/handlers.test.ts``) and are not
exercised by this pytest module.
"""

from __future__ import annotations


class TestAC3ValidFixtures:
    """AC-3: validate_fixtures.py passes on valid fixtures."""

    def test_valid_fixtures_pass(self):
        from tests.unit.infra.test_validate_fixtures import (
            test_valid_fixtures_pass,
        )

        test_valid_fixtures_pass()


class TestAC3InvalidFixtureFails:
    """AC-3: validate_fixtures.py exits non-zero on malformed fixture."""

    def test_invalid_fixture_fails(self, tmp_path, monkeypatch):
        from tests.unit.infra.test_validate_fixtures import (
            test_invalid_fixture_fails,
        )

        test_invalid_fixture_fails(tmp_path, monkeypatch)
