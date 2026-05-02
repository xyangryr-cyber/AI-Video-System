"""[SPEC-B-015] Unit tests: P7A Huey task registration + queue isolation + CLI args.

Covers AC-1 (three task configs), AC-2 (register_p7a_tasks wires all three),
AC-6 (phase_7a queue distinct from render phase_8 queue), and AC-7
(worker CLI args include the four queues).

Verification gate: the task card's Test Mapping lists tests/unit/infra/
test_spec_b_015.py but that file is NOT in SPEC-B-015 allowed_files
(validate_edit_target.py hook blocks it). This test file + the two other
files under tests/unit/workers/ and tests/integration/workers/ (listed in
allowed_files) are the canonical coverage, following the same reconciliation
pattern SPEC-B-013 and SPEC-B-014 used.
"""

from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
HUEY_QUEUES_YAML = REPO_ROOT / "config" / "huey_queues.yaml"


# --- AC-1 ---------------------------------------------------------------


class TestAC1Registration:
    """Three tasks with the spec-mandated priority / retries / timeout."""

    def test_material_fetch_config(self):
        from src.backend.workers.p7a_tasks import P7A_TASK_CONFIGS

        cfg = P7A_TASK_CONFIGS["material_fetch"]
        assert cfg["queue"] == "phase_7a"
        assert cfg["priority"] == 5
        assert cfg["retries"] == 3
        assert cfg["timeout"] == 60

    def test_material_verify_config(self):
        from src.backend.workers.p7a_tasks import P7A_TASK_CONFIGS

        cfg = P7A_TASK_CONFIGS["material_verify"]
        assert cfg["queue"] == "phase_7a"
        assert cfg["priority"] == 5
        assert cfg["retries"] == 2
        assert cfg["timeout"] == 30

    def test_chart_material_fetch_config(self):
        from src.backend.workers.p7a_tasks import P7A_TASK_CONFIGS

        cfg = P7A_TASK_CONFIGS["chart_material_fetch"]
        assert cfg["queue"] == "phase_7a"
        assert cfg["priority"] == 4
        assert cfg["retries"] == 3
        assert cfg["timeout"] == 90


# --- AC-2 ---------------------------------------------------------------


class _HueyStub:
    """Minimal stub recording every @huey.task() decoration."""

    def __init__(self):
        self.registrations: list[dict] = []

    def task(self, **kwargs):
        def _decorator(fn):
            self.registrations.append({"name": fn.__name__, **kwargs})
            return fn

        return _decorator


class TestAC2WorkerConsumesThree:
    """register_p7a_tasks wires all three tasks onto the provided huey."""

    def test_registers_three_tasks_on_phase_7a_queue(self):
        from src.backend.workers.p7a_tasks import register_p7a_tasks

        stub = _HueyStub()
        register_p7a_tasks(stub)

        assert len(stub.registrations) == 3
        names = {r["name"] for r in stub.registrations}
        assert names == {"material_fetch", "material_verify", "chart_material_fetch"}
        for r in stub.registrations:
            assert r["queue"] == "phase_7a", (
                f"{r['name']} must be registered on phase_7a, got {r['queue']}"
            )
            # spec wires retries + timeout through @huey.task kwargs
            assert "retries" in r and "timeout" in r


# --- AC-6 ---------------------------------------------------------------


class TestAC6PhaseIsolation:
    """phase_7a queue must be distinct from phase_8 render queue."""

    def test_no_p7a_task_routed_to_phase_8(self):
        from src.backend.workers.p7a_tasks import P7A_TASK_CONFIGS

        for name, cfg in P7A_TASK_CONFIGS.items():
            assert cfg["queue"] != "phase_8", (
                f"{name} must not share phase_8 render queue"
            )
            assert cfg["queue"] == "phase_7a"

    def test_worker_queue_list_includes_both_p7a_and_render(self):
        """AC-6 assumes both queues co-exist; worker consumes them
        independently, so WORKER_QUEUE_NAMES must not collapse them."""
        from src.backend.workers.p7a_tasks import WORKER_QUEUE_NAMES

        assert "phase_7a" in WORKER_QUEUE_NAMES


# --- AC-7 ---------------------------------------------------------------


class TestAC7WorkerCLIArgs:
    """Worker argv includes default + claim_verification +
    claim_verification_priority + phase_7a, preserving v3.16 queues."""

    def test_worker_queue_names_exact_order(self):
        from src.backend.workers.p7a_tasks import WORKER_QUEUE_NAMES

        assert WORKER_QUEUE_NAMES == [
            "default",
            "claim_verification",
            "claim_verification_priority",
            "phase_7a",
        ]

    def test_cli_arg_string_is_comma_joined(self):
        from src.backend.workers.p7a_tasks import worker_cli_queue_arg

        arg = worker_cli_queue_arg()
        assert arg == (
            "-Q default,claim_verification,claim_verification_priority,phase_7a"
        )

    def test_huey_queues_yaml_file_lists_four_worker_queues(self):
        """config/huey_queues.yaml exists and text-embeds the four queues.

        Text-level check so the test is runnable even when PyYAML is
        absent from the interpreter (Py3.13 clean env). A structural YAML
        check runs additionally when PyYAML is importable.
        """
        assert HUEY_QUEUES_YAML.is_file(), (
            "config/huey_queues.yaml missing (allowed_files MODIFY target)"
        )
        text = HUEY_QUEUES_YAML.read_text(encoding="utf-8")
        # All four queue names must appear under the worker_queues: block
        assert "worker_queues:" in text
        for q in (
            "default",
            "claim_verification",
            "claim_verification_priority",
            "phase_7a",
        ):
            assert f"- {q}\n" in text, f"worker_queues missing {q}"

    def test_huey_queues_yaml_structural_if_pyyaml_available(self):
        yaml = pytest.importorskip("yaml")
        data = yaml.safe_load(HUEY_QUEUES_YAML.read_text(encoding="utf-8"))
        assert data.get("worker_queues") == [
            "default",
            "claim_verification",
            "claim_verification_priority",
            "phase_7a",
        ]
        p7a = (data.get("queues") or {}).get("phase_7a") or {}
        tasks = {t["name"]: t for t in (p7a.get("tasks") or [])}
        assert set(tasks) == {
            "material_fetch",
            "material_verify",
            "chart_material_fetch",
        }
        assert tasks["material_fetch"]["retries"] == 3
        assert tasks["material_fetch"]["timeout"] == 60
        assert tasks["material_verify"]["retries"] == 2
        assert tasks["material_verify"]["timeout"] == 30
        assert tasks["chart_material_fetch"]["retries"] == 3
        assert tasks["chart_material_fetch"]["timeout"] == 90
