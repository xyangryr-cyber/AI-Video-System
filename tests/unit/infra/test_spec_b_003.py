"""Tests for [SPEC-B-003] Huey(SqliteHuey) Worker Queue Setup.

Config-first strategy: the heartbeat/scan/timeout numbers AC-3..AC-6
require are pure constants, so these tests import them directly. AC-7
verifies the source wires ``SqliteHuey`` against ``data/db/`` without
instantiating Huey (Huey is not a unit-test dep); an optional runtime
sanity test runs only if ``huey`` is installed.

Package-layout note: SPEC-B-001 already committed the directory as
``src/backend/workers/`` (plural). The B-003 task card's snippet
``src/backend/worker/`` is treated as a typo and implemented under
``workers/`` so docker-compose's ``python -m src.backend.workers.run``
entrypoint keeps working.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
HUEY_CONFIG_FILE = REPO_ROOT / "src" / "backend" / "workers" / "huey_config.py"
WORKER_RUN_FILE = REPO_ROOT / "src" / "backend" / "workers" / "run.py"
COMPOSE_FILE = REPO_ROOT / "docker-compose.yml"
SCHEMA_FILE = REPO_ROOT / "src" / "backend" / "db" / "schema.sql"
DB_DIR = REPO_ROOT / "data" / "db"


def _worker_service_body() -> str:
    text = COMPOSE_FILE.read_text(encoding="utf-8")
    m = re.search(
        r"^  worker:\n(?P<body>(?:    .*\n|\n)+?)(?=^  \S|^\S|\Z)",
        text,
        re.MULTILINE,
    )
    assert m is not None, "worker service missing in docker-compose.yml"
    return m.group("body")


# ---- AC-1 ------------------------------------------------------------------


class TestAC1NoLegacyTaskQueueTable:
    """AC-1: `data/db/` 中无旧版 `task_queue` 表."""

    def test_no_task_queue_table_in_schema(self):
        text = SCHEMA_FILE.read_text(encoding="utf-8")
        assert "task_queue" not in text.lower(), (
            "Legacy 'task_queue' table must not exist in schema.sql"
        )

    def test_no_legacy_task_queue_files_in_data_db(self):
        if not DB_DIR.exists():
            return
        strays = [p.name for p in DB_DIR.iterdir() if "task_queue" in p.name.lower()]
        assert not strays, f"Legacy task_queue artefacts remain in data/db/: {strays}"


# ---- AC-2 ------------------------------------------------------------------


class TestAC2WorkerStartupCommand:
    """AC-2: Worker 启动命令为 `huey_consumer` 或等效."""

    def test_worker_command_declared(self):
        body = _worker_service_body()
        assert "command:" in body, "worker service must declare command"

    def test_worker_command_is_huey_consumer_or_equivalent(self):
        body = _worker_service_body()
        cmd_lines = [line for line in body.splitlines() if "command:" in line]
        assert cmd_lines, "worker command: directive missing"
        cmd = cmd_lines[0]

        direct = "huey_consumer" in cmd
        indirect = False
        if "python" in cmd and "src.backend.workers" in cmd:
            assert WORKER_RUN_FILE.is_file(), (
                "docker-compose references workers module but "
                f"{WORKER_RUN_FILE} missing"
            )
            run_text = WORKER_RUN_FILE.read_text(encoding="utf-8")
            indirect = (
                "huey_consumer" in run_text
                or re.search(r"from\s+huey", run_text) is not None
            )
        assert direct or indirect, (
            f"worker command must be huey_consumer-equivalent: {cmd!r}"
        )


# ---- AC-3 ------------------------------------------------------------------


class TestAC3HeartbeatAndScanParams:
    """AC-3: heartbeat=5s, scan=30s 参数配置正确."""

    def test_heartbeat_is_5_seconds(self):
        from src.backend.workers.huey_config import HEARTBEAT_SEC

        assert HEARTBEAT_SEC == 5

    def test_scan_interval_is_30_seconds(self):
        from src.backend.workers.huey_config import SCAN_INTERVAL_SEC

        assert SCAN_INTERVAL_SEC == 30


# ---- AC-4 ------------------------------------------------------------------


class TestAC4StaleThresholdCalculation:
    """AC-4: stale_threshold 计算为 task_timeout + 60s."""

    def test_grace_is_60_seconds(self):
        from src.backend.workers.huey_config import STALE_THRESHOLD_GRACE_SEC

        assert STALE_THRESHOLD_GRACE_SEC == 60

    def test_stale_threshold_adds_grace_to_each_timeout(self):
        from src.backend.workers.huey_config import (
            TASK_TIMEOUTS,
            stale_threshold_for,
        )

        for task_type, timeout in TASK_TIMEOUTS.items():
            assert stale_threshold_for(task_type) == timeout + 60, (
                f"stale_threshold({task_type}) must be timeout+60"
            )

    def test_stale_threshold_rejects_unknown_task_type(self):
        from src.backend.workers.huey_config import stale_threshold_for

        with pytest.raises(KeyError):
            stale_threshold_for("unknown_task_type")


# ---- AC-5 ------------------------------------------------------------------


class TestAC5DefaultMaxAttempts:
    """AC-5: default_max_attempts=3."""

    def test_default_max_attempts_is_3(self):
        from src.backend.workers.huey_config import DEFAULT_MAX_ATTEMPTS

        assert DEFAULT_MAX_ATTEMPTS == 3


# ---- AC-6 ------------------------------------------------------------------


class TestAC6TaskTimeoutValues:
    """AC-6: 超时值 tts=600s, keyframe=1800s, rough=1800s, final=2400s."""

    def test_task_timeouts_exact(self):
        from src.backend.workers.huey_config import TASK_TIMEOUTS

        assert TASK_TIMEOUTS == {
            "tts": 600,
            "bgm": 600,
            "sfx": 600,
            "keyframe": 1800,
            "rough": 1800,
            "final": 2400,
        }


# ---- AC-7 ------------------------------------------------------------------


class TestAC7SqliteHueyBackend:
    """AC-7: Huey 使用 SqliteHuey 后端，DB 文件在 `data/db/` 目录."""

    def test_huey_config_wires_sqlite_huey(self):
        text = HUEY_CONFIG_FILE.read_text(encoding="utf-8")
        assert "SqliteHuey" in text, (
            "huey_config.py must reference SqliteHuey as the backend"
        )

    def test_default_db_dir_is_data_db(self):
        from src.backend.workers.huey_config import DEFAULT_DB_DIR

        # Normalise to forward slashes for cross-platform parity.
        assert str(DEFAULT_DB_DIR).replace("\\", "/") == "data/db"

    def test_huey_db_filename_suffix(self):
        from src.backend.workers.huey_config import DEFAULT_HUEY_DB_FILE

        assert DEFAULT_HUEY_DB_FILE.endswith(
            ".sqlite3"
        ) or DEFAULT_HUEY_DB_FILE.endswith(".db"), (
            "Huey DB file must be a SQLite DB (.sqlite3 or .db)"
        )

    def test_build_huey_instantiates_when_package_available(self, tmp_path):
        """Optional runtime check: only runs if huey is installed."""
        try:
            import huey  # noqa: F401
        except ImportError:
            pytest.skip(
                "huey package not installed in this env; "
                "source-level wiring already verified above"
            )
        from src.backend.workers.huey_config import build_huey

        inst = build_huey(db_dir=tmp_path)
        assert type(inst).__name__ == "SqliteHuey"
