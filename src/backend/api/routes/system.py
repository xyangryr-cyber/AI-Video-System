"""SPEC-B-009 Pre-flight routes.

Exposes:

* ``GET /status`` -- latest system_status rows (SPEC-1A row
  for `/api/system/status`). Shape: ``{checks: SystemCheck[]}``.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter, Depends

from src.backend.db.repositories.system_status_repo import (
    SystemStatusRepository,
)

router = APIRouter(prefix="/api/system", tags=["system"])


def get_db() -> sqlite3.Connection:  # pragma: no cover -- app wiring
    """Overridden via ``app.dependency_overrides[get_db]`` in tests and
    by the production startup hook."""
    raise RuntimeError(
        "DB dependency not wired. Override get_db in the app startup hook or in tests."
    )


@router.get("/status")
def get_system_status(db: sqlite3.Connection = Depends(get_db)) -> dict[str, Any]:
    repo = SystemStatusRepository(db)
    return {
        "checks": [
            {
                "check_name": r["check_name"],
                "status": r["status"],
                "message": r["message"],
                "checked_at": r["checked_at"],
                "valid_until": r["valid_until"],
            }
            for r in repo.latest_all()
        ]
    }
