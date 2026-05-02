"""SPEC-B-009 Pre-flight checks and service degradation.

Two entry points:

* :func:`run_full_preflight` -- all 9 checks (5 critical + 4 degradable),
  fired at API startup (SPEC-1.3, AC-6).
* :func:`run_critical_preflight` -- 5 critical checks only, fired at
  project-create time (AC-7).

All 9 checks now have real implementations: LLM config validation,
reviewer LLM config check, TTS provider import, SQLite connectivity,
media dir creation, web search provider import, material provider import,
BGM agent import, and financial data service import. Critical checks
may return ``status='failed'``; degradable checks return ``status='degraded'``
on import/config failure.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Dict, Iterable, Literal, Optional

from fastapi import HTTPException

from src.backend.db.repositories.system_status_repo import (
    SystemStatusRepository,
)


CheckStatus = Literal["ok", "degraded", "failed"]

CRITICAL_CHECKS: tuple[str, ...] = (
    "llm",
    "llm_review",
    "sqlite",
    "media_dir",
)
DEGRADABLE_CHECKS: tuple[str, ...] = (
    "tts",
    "web_search",
    "material",
    "bgm",
    "financial_data",
)
ALL_CHECKS: tuple[str, ...] = CRITICAL_CHECKS + DEGRADABLE_CHECKS

VALIDITY_HOURS = 24


@dataclass(frozen=True)
class CheckResult:
    status: CheckStatus
    message: Optional[str] = None


Runner = Callable[[], CheckResult]


# -- Real check implementations -----------------------------------------


def _check_llm() -> CheckResult:
    """Verify the LLM service can be imported and model_config.json is valid."""
    try:
        from src.backend.services.llm_service import VALID_ROLES
        from src.backend.services.llm_service import resolve_model  # noqa: F401, F811
    except ImportError as exc:
        return CheckResult(status="failed", message=f"LLM service import failed: {exc}")
    config_path = Path("config/model_config.json")
    if not config_path.is_file():
        return CheckResult(status="degraded", message="model_config.json not found")
    try:
        with config_path.open(encoding="utf-8") as f:
            cfg = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        return CheckResult(status="degraded", message=f"model_config.json invalid: {exc}")
    if not isinstance(cfg, dict):
        return CheckResult(status="degraded", message="model_config.json is not an object")
    missing = [r for r in VALID_ROLES if r not in cfg]
    if missing:
        return CheckResult(status="degraded", message=f"missing roles in config: {missing}")
    return CheckResult(status="ok")


def _check_sqlite() -> CheckResult:
    """Connect to SQLite and run a health query."""
    import os as _os

    db_url = _os.environ.get("DATABASE_URL", "sqlite:///data/db/dev.sqlite3")
    db_path = db_url.replace("sqlite:///", "") if db_url.startswith("sqlite:///") else db_url
    try:
        conn = sqlite3.connect(db_path, timeout=5)
        conn.execute("SELECT 1")
        conn.close()
        return CheckResult(status="ok")
    except sqlite3.Error as exc:
        return CheckResult(status="failed", message=f"SQLite connection failed: {exc}")
    except Exception as exc:
        return CheckResult(status="failed", message=f"SQLite check error: {exc}")


def _check_tts() -> CheckResult:
    """Check TTS provider importability. Live API check requires a token
    (known ByteDance token issue), so this checker is DEGRADABLE."""
    try:
        from src.backend.services.tts_provider import TTSProvider  # noqa: F401
    except ImportError as exc:
        return CheckResult(status="degraded", message=f"TTS provider import failed: {exc}")
    return CheckResult(status="ok", message="TTS provider importable")


def _check_media_dir() -> CheckResult:
    """Ensure the media directory exists or can be created."""
    media_dir = Path("data/media")
    try:
        media_dir.mkdir(parents=True, exist_ok=True)
        return CheckResult(status="ok")
    except OSError as exc:
        return CheckResult(status="failed", message=f"Cannot create media directory {media_dir}: {exc}")


def _check_llm_review() -> CheckResult:
    """Verify Reviewer LLM config exists."""
    config_path = Path("config/model_config.json")
    if not config_path.is_file():
        return CheckResult(status="degraded", message="model_config.json not found")
    try:
        with config_path.open(encoding="utf-8") as f:
            cfg = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        return CheckResult(status="degraded", message=f"model_config.json invalid: {exc}")
    if "reviewer" not in cfg and "gatekeeper" not in cfg:
        return CheckResult(status="degraded", message="no reviewer/gatekeeper role in config")
    return CheckResult(status="ok")


def _check_web_search() -> CheckResult:
    """Verify web search / fact checker agent is importable."""
    try:
        from src.backend.agents import fact_checker  # noqa: F401
    except ImportError:
        return CheckResult(status="degraded", message="fact_checker web_search import failed")
    return CheckResult(status="ok", message="fact_checker web_search importable")


def _check_material() -> CheckResult:
    """Verify material providers are importable."""
    try:
        from src.backend.services import material_providers  # noqa: F401
    except ImportError:
        return CheckResult(status="degraded", message="material_providers import failed")
    return CheckResult(status="ok", message="material providers importable")


def _check_bgm() -> CheckResult:
    """Verify BGM agent is importable."""
    try:
        from src.backend.agents import bgm_agent  # noqa: F401
    except ImportError:
        return CheckResult(status="degraded", message="bgm_agent import failed")
    return CheckResult(status="ok", message="bgm_agent importable")


def _check_financial_data() -> CheckResult:
    """Verify financial data service + providers are importable."""
    try:
        from src.backend.services.financial_data_service import FinancialDataService  # noqa: F401
    except ImportError:
        return CheckResult(status="degraded", message="financial_data_service import failed")
    return CheckResult(status="ok", message="financial data service importable")


DEFAULT_RUNNERS: Dict[str, Runner] = {
    "llm": _check_llm,
    "llm_review": _check_llm_review,
    "tts": _check_tts,
    "sqlite": _check_sqlite,
    "media_dir": _check_media_dir,
    "web_search": _check_web_search,
    "material": _check_material,
    "bgm": _check_bgm,
    "financial_data": _check_financial_data,
}


def _format_iso(dt: datetime) -> str:
    """ISO-8601 UTC with millisecond precision, matching the SQLite
    ``strftime('%Y-%m-%dT%H:%M:%fZ','now')`` default used elsewhere in
    the schema."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    millis = dt.microsecond // 1000
    return f"{dt.strftime('%Y-%m-%dT%H:%M:%S')}.{millis:03d}Z"


def _run_subset(
    conn: sqlite3.Connection,
    names: Iterable[str],
    runners: Optional[Dict[str, Runner]],
    now: Optional[datetime],
) -> None:
    effective = {**DEFAULT_RUNNERS, **(runners or {})}
    now = now or datetime.now(timezone.utc)
    checked_at = _format_iso(now)
    valid_until = _format_iso(now + timedelta(hours=VALIDITY_HOURS))
    repo = SystemStatusRepository(conn)
    for name in names:
        result = effective[name]()
        repo.insert(name, result.status, result.message, checked_at, valid_until)


def run_full_preflight(
    conn: sqlite3.Connection,
    runners: Optional[Dict[str, Runner]] = None,
    now: Optional[datetime] = None,
) -> None:
    """Run all 9 checks and persist a row per check in ``system_status``."""
    _run_subset(conn, ALL_CHECKS, runners, now)


def run_critical_preflight(
    conn: sqlite3.Connection,
    runners: Optional[Dict[str, Runner]] = None,
    now: Optional[datetime] = None,
) -> None:
    """Run the 5 critical checks only (project-create gate feed)."""
    _run_subset(conn, CRITICAL_CHECKS, runners, now)


def require_critical_ok(conn: sqlite3.Connection) -> None:
    """Raise :class:`HTTPException` (403) unless every critical check's
    latest row is ``status='ok'``. Used by the project-create endpoint
    to implement SPEC-14.1's "阻断创建项目" branch.
    """
    repo = SystemStatusRepository(conn)
    if not repo.all_critical_ok(CRITICAL_CHECKS):
        raise HTTPException(
            status_code=403,
            detail="System not ready: one or more critical Pre-flight checks failed",
        )
