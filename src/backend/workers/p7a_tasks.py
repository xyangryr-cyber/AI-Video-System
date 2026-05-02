"""[SPEC-B-015] Huey worker tasks for P7A (MaterialFetcher /
MaterialVerifier / ChartMaterialFetcher).

Three tasks registered on the ``phase_7a`` queue:

+---------------------+----------+---------+---------+
| task                | priority | retries | timeout |
+=====================+==========+=========+=========+
| material_fetch      |    5     |    3    |   60s   |
| material_verify     |    5     |    2    |   30s   |
| chart_material_fetch|    4     |    3    |   90s   |
+---------------------+----------+---------+---------+

Queue isolation: phase_7a is independent from the v3.16 ``claim_verification``
/ ``claim_verification_priority`` queues (B-BDD-1.1) and from the phase_8
render queue (SPEC-F), so P7A fetch/verify latency cannot block rendering.

Per-provider throttling lives in ``p7a_throttle.ProviderThrottle``; each
@huey.task wrapper must acquire a slot before invoking the provider SDK.

Agent implementations (the ``_impl`` function bodies beyond fetch_with_retry)
are the responsibility of C-021; this module provides the worker plumbing:
task registration metadata, CLI arg builder, retry/terminal-handler, and
the async_tasks ledger writer.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from pathlib import Path
from typing import Any

# ---------- AC-1: task configs -----------------------------------------

P7A_TASK_CONFIGS: dict[str, dict[str, Any]] = {
    "material_fetch": {
        "queue": "phase_7a",
        "priority": 5,
        "retries": 3,
        "timeout": 60,
    },
    "material_verify": {
        "queue": "phase_7a",
        "priority": 5,
        "retries": 2,
        "timeout": 30,
    },
    "chart_material_fetch": {
        "queue": "phase_7a",
        "priority": 4,
        "retries": 3,
        "timeout": 90,
    },
}

# ---------- AC-7: worker CLI queue list --------------------------------

WORKER_QUEUE_NAMES: list[str] = [
    "default",
    "claim_verification",
    "claim_verification_priority",
    "phase_7a",
]


def worker_cli_queue_arg() -> str:
    """Return the ``-Q`` argument passed to ``huey_consumer``."""
    return "-Q " + ",".join(WORKER_QUEUE_NAMES)


# ---------- AC-2: Huey task registration --------------------------------


class TransientProviderError(Exception):
    """Raised by provider SDKs on 5xx responses; triggers Huey retry."""

    def __init__(self, msg: str, status_code: int = 0) -> None:
        super().__init__(msg)
        self.status_code = status_code


class FetchExhaustedError(Exception):
    """Raised after ``max_attempts`` transient failures. The manifest has
    already been marked ``verification_status=missing`` by this point."""


def _material_fetch_task(*args: Any, **kwargs: Any) -> None:
    """Placeholder body. C-021 replaces with real MaterialFetcher call."""
    raise NotImplementedError("material_fetch body lands in SPEC-C-021")


def _material_verify_task(*args: Any, **kwargs: Any) -> None:
    raise NotImplementedError("material_verify body lands in SPEC-C-021")


def _chart_material_fetch_task(*args: Any, **kwargs: Any) -> None:
    raise NotImplementedError("chart_material_fetch body lands in SPEC-C-021")


_TASK_IMPLS = {
    "material_fetch": _material_fetch_task,
    "material_verify": _material_verify_task,
    "chart_material_fetch": _chart_material_fetch_task,
}


def register_p7a_tasks(huey: Any) -> dict[str, Any]:
    """Decorate the three P7A task bodies with ``@huey.task`` using the
    spec-mandated queue / retries / timeout kwargs.

    Returns a dict of task_name -> decorated callable so callers (e.g.
    the workers package ``__init__``) can hold a reference if they need
    to enqueue tasks programmatically.
    """
    registered: dict[str, Any] = {}
    for name, cfg in P7A_TASK_CONFIGS.items():
        impl = _TASK_IMPLS[name]
        impl.__name__ = name  # ensure registration name matches task key
        decorated = huey.task(
            queue=cfg["queue"],
            priority=cfg["priority"],
            retries=cfg["retries"],
            timeout=cfg["timeout"],
        )(impl)
        registered[name] = decorated
    return registered


# ---------- AC-4: fetch with retry + terminal missing-write -------------


def fetch_with_retry(
    *,
    provider: Any,
    manifest_path: Path,
    material_id: str,
    max_attempts: int = 3,
) -> Any:
    """Call ``provider.fetch(material_id)`` up to ``max_attempts`` times.

    * On ``TransientProviderError`` (5xx): retry until attempts exhausted,
      then mark ``verification_status='missing'`` in the manifest at
      ``manifest_path`` and raise ``FetchExhaustedError``.
    * On any other exception: propagate immediately (no retry, no
      manifest mutation).
    """
    last_err: Exception | None = None
    for attempt in range(max_attempts):
        try:
            return provider.fetch(material_id)
        except TransientProviderError as err:
            last_err = err
            if attempt == max_attempts - 1:
                _mark_material_missing(manifest_path, material_id)
                raise FetchExhaustedError(
                    f"material_id={material_id} failed after {max_attempts} attempts: {err}"
                ) from err
            # else: try again
    # Unreachable; the loop either returns, raises TransientProviderError
    # on non-final attempts (handled by outer except), or raises
    # FetchExhaustedError on the final attempt.
    raise FetchExhaustedError(  # pragma: no cover
        f"material_id={material_id}: unexpected fall-through ({last_err})"
    )


def _mark_material_missing(manifest_path: Path, material_id: str) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    materials = manifest.setdefault("materials", {})
    entry = materials.setdefault(material_id, {"material_id": material_id})
    entry["verification_status"] = "missing"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ---------- AC-5: async_tasks ledger row per Huey invocation -----------


def record_huey_task(
    conn: sqlite3.Connection,
    *,
    task_id: str,
    project_id: str,
    phase: int,
    task_type: str,
    params: Mapping[str, Any] | None = None,
    ledger_task_id: str | None = None,
) -> None:
    """Insert one ``async_tasks`` row per P7A Huey invocation.

    SPEC-B-015 AC-5 calls this a "task_ledger record"; reconciled against
    the DDL (V005), ``task_ledger.type`` CHECK does not include
    ``material_fetch`` / ``material_verify``, whereas ``async_tasks.type``
    is unrestricted. The row written here is the one-to-one record the
    AC demands; optional ``ledger_task_id`` still links back to an
    upstream ``task_ledger`` row when a v3.16 BDD-typed parent exists.
    """
    if task_type not in P7A_TASK_CONFIGS:
        raise ValueError(
            f"record_huey_task only accepts P7A task types "
            f"{sorted(P7A_TASK_CONFIGS)}; got {task_type!r}"
        )
    max_attempts = P7A_TASK_CONFIGS[task_type]["retries"]
    conn.execute(
        "INSERT INTO async_tasks "
        "(task_id, project_id, phase, ledger_task_id, type, params, "
        " max_attempts) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            task_id,
            project_id,
            phase,
            ledger_task_id,
            task_type,
            json.dumps(dict(params or {}), ensure_ascii=False),
            max_attempts,
        ),
    )
    conn.commit()


__all__ = [
    "P7A_TASK_CONFIGS",
    "WORKER_QUEUE_NAMES",
    "TransientProviderError",
    "FetchExhaustedError",
    "register_p7a_tasks",
    "worker_cli_queue_arg",
    "fetch_with_retry",
    "record_huey_task",
]
