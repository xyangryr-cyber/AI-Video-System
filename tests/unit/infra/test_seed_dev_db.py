"""SPEC-B-018 AC-2: seed_dev_db inserts >=12 demo projects covering all phases."""

from __future__ import annotations

import importlib
import sqlite3
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]


@pytest.fixture
def db_path(tmp_path) -> Path:
    p = tmp_path / "dev.sqlite3"
    return p


def _seed(db_path: Path):
    import sys

    sys.path.insert(0, str(REPO))
    mod = importlib.import_module("scripts.seed_dev_db")
    mod.seed(db_path)


def _phase_rows(db_path: Path) -> list[int]:
    con = sqlite3.connect(db_path)
    try:
        return sorted(r[0] for r in con.execute("select current_phase from projects"))
    finally:
        con.close()


def test_seeds_twelve_phases(db_path):
    _seed(db_path)
    phases = _phase_rows(db_path)
    assert len(phases) >= 12
    assert set(range(0, 12)).issubset(set(phases)), (
        f"missing phases: {set(range(0, 12)) - set(phases)}"
    )


def test_seeds_idempotent(db_path):
    _seed(db_path)
    first = _phase_rows(db_path)
    _seed(db_path)
    second = _phase_rows(db_path)
    assert first == second, (
        "second seed run produced different rows (must be idempotent)"
    )
