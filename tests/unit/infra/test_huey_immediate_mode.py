"""Tests for huey immediate mode and enqueue runner factory.

SPEC-G-000b: build_huey(immediate=True) + huey_enqueue_runner factory.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.backend.workers.huey_config import build_huey, huey_enqueue_runner


@pytest.fixture
def temp_db_dir(tmp_path: Path) -> Path:
    return tmp_path / "huey_test"


def test_build_huey_immediate_mode(temp_db_dir: Path) -> None:
    """AC-1: build_huey(immediate=True) returns SqliteHuey with immediate=True."""
    huey = build_huey(db_dir=temp_db_dir, immediate=True)
    assert huey.immediate is True


def test_build_huey_default_not_immediate(temp_db_dir: Path) -> None:
    """AC-1: build_huey() without immediate defaults to False."""
    huey = build_huey(db_dir=temp_db_dir)
    assert not huey.immediate


def test_huey_enqueue_runner_dispatches(temp_db_dir: Path) -> None:
    """AC-2: runner looks up task_type in registry and calls task_fn(task_id, params)."""
    huey = build_huey(db_dir=temp_db_dir, immediate=True)
    side_effects: list[tuple[str, dict]] = []

    @huey.task()
    def my_task(task_id: str, params: dict) -> None:
        side_effects.append((task_id, params))

    registry = {"my_type": my_task}
    runner = huey_enqueue_runner(huey, registry)
    runner("my_type", "task_1", {"key": "val"})

    assert side_effects == [("task_1", {"key": "val"})]


def test_immediate_mode_executes_synchronously(temp_db_dir: Path) -> None:
    """AC-3: immediate=True -> task side effect is visible immediately."""
    huey = build_huey(db_dir=temp_db_dir, immediate=True)
    side_effects: list[str] = []

    @huey.task()
    def sync_task(task_id: str, params: dict) -> None:
        side_effects.append(task_id)

    registry = {"sync": sync_task}
    runner = huey_enqueue_runner(huey, registry)
    runner("sync", "test_id", {})

    assert side_effects == ["test_id"]


def test_default_mode_queues_only(temp_db_dir: Path) -> None:
    """AC-3: immediate=False -> task goes into queue, side effect NOT visible."""
    huey = build_huey(db_dir=temp_db_dir, immediate=False)
    side_effects: list[str] = []

    @huey.task()
    def queued_task(task_id: str, params: dict) -> None:
        side_effects.append(task_id)

    registry = {"queue": queued_task}
    runner = huey_enqueue_runner(huey, registry)
    runner("queue", "test_id", {})

    assert side_effects == []
