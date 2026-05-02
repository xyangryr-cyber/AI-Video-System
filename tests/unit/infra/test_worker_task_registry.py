"""Tests for [SPEC-G-000c] 6 phase huey task registration + registry.

Verifies that tasks.py exposes:
- 6 @huey.task() placeholder functions (AC-1)
- TASK_REGISTRY mapping task_type -> task function (AC-2)
- TASK_TIMEOUTS includes bgm and sfx (AC-3, AC-5)
"""

from __future__ import annotations


EXPECTED_TASK_TYPES = [
    "generate_narration",
    "preview_mix",
    "plan_layout",
    "render_keyframes",
    "compose_rough_cut",
    "export_final",
]

EXPECTED_FUNC_NAMES = [
    "run_phase4_tts",
    "run_phase5_bgm_preview",
    "run_phase6_sfx_layout",
    "run_phase8_keyframe",
    "run_phase10_rough_cut",
    "run_phase11_final_cut",
]


# ---- AC-1: All 6 tasks registered ---------------------------------------


def test_all_6_tasks_registered():
    """AC-1: TASK_REGISTRY contains exactly 6 expected task_type keys."""
    from src.backend.workers.tasks import TASK_REGISTRY

    assert isinstance(TASK_REGISTRY, dict), "TASK_REGISTRY must be a dict"
    assert len(TASK_REGISTRY) == 6, (
        f"Expected 6 entries, got {len(TASK_REGISTRY)}: {list(TASK_REGISTRY.keys())}"
    )
    for task_type in EXPECTED_TASK_TYPES:
        assert task_type in TASK_REGISTRY, (
            f"TASK_REGISTRY missing expected key: {task_type!r}"
        )


# ---- AC-2: Registry maps each task_type correctly -----------------------


def test_registry_maps_each_task_type():
    """AC-2: Each task_type maps to the correct callable by name."""
    from src.backend.workers.tasks import TASK_REGISTRY

    for task_type, expected_name in zip(EXPECTED_TASK_TYPES, EXPECTED_FUNC_NAMES):
        task_fn = TASK_REGISTRY[task_type]
        assert callable(task_fn), (
            f"TASK_REGISTRY[{task_type!r}] must be callable, got {type(task_fn)}"
        )
        # Huey TaskWrapper stores the underlying function in .func
        raw_fn = getattr(task_fn, "func", task_fn)
        actual_name = getattr(raw_fn, "__name__", "")
        assert actual_name == expected_name, (
            f"TASK_REGISTRY[{task_type!r}] func name {actual_name!r} "
            f"!= expected {expected_name!r}"
        )


def test_registry_callables_have_correct_names():
    """AC-2: Each TASK_REGISTRY callable has the correct __name__.

    Verifies that tasks.py imports correctly at module level (all agent
    imports are top-level) and that each registered task function has
    the expected name.
    """
    from src.backend.workers.tasks import TASK_REGISTRY

    for task_type, expected_name in zip(EXPECTED_TASK_TYPES, EXPECTED_FUNC_NAMES):
        task_fn = TASK_REGISTRY[task_type]
        raw_fn = getattr(task_fn, "func", None)
        assert raw_fn is not None, (
            f"TASK_REGISTRY[{task_type!r}] has no .func; expected a huey TaskWrapper"
        )
        actual_name = getattr(raw_fn, "__name__", "")
        assert actual_name == expected_name, (
            f"TASK_REGISTRY[{task_type!r}] func name {actual_name!r} "
            f"!= expected {expected_name!r}"
        )


# ---- AC-3: TASK_TIMEOUTS has bgm and sfx --------------------------------


def test_task_timeouts_has_bgm_and_sfx():
    """AC-3: TASK_TIMEOUTS contains bgm=600 and sfx=600."""
    from src.backend.workers.huey_config import TASK_TIMEOUTS

    assert "bgm" in TASK_TIMEOUTS, (
        f"TASK_TIMEOUTS missing 'bgm' key, got: {list(TASK_TIMEOUTS.keys())}"
    )
    assert "sfx" in TASK_TIMEOUTS, (
        f"TASK_TIMEOUTS missing 'sfx' key, got: {list(TASK_TIMEOUTS.keys())}"
    )
    assert TASK_TIMEOUTS["bgm"] == 600, f"Expected bgm=600, got {TASK_TIMEOUTS['bgm']}"
    assert TASK_TIMEOUTS["sfx"] == 600, f"Expected sfx=600, got {TASK_TIMEOUTS['sfx']}"


# ---- AC-5: stale_threshold_for no longer KeyError -----------------------


def test_stale_threshold_for_bgm_no_keyerror():
    """AC-5: stale_threshold_for('bgm') returns timeout + grace, no KeyError."""
    from src.backend.workers.huey_config import (
        STALE_THRESHOLD_GRACE_SEC,
        TASK_TIMEOUTS,
        stale_threshold_for,
    )

    result = stale_threshold_for("bgm")
    assert result == TASK_TIMEOUTS["bgm"] + STALE_THRESHOLD_GRACE_SEC


def test_stale_threshold_for_sfx_no_keyerror():
    """AC-5: stale_threshold_for('sfx') returns timeout + grace, no KeyError."""
    from src.backend.workers.huey_config import (
        STALE_THRESHOLD_GRACE_SEC,
        TASK_TIMEOUTS,
        stale_threshold_for,
    )

    result = stale_threshold_for("sfx")
    assert result == TASK_TIMEOUTS["sfx"] + STALE_THRESHOLD_GRACE_SEC
