"""Observability API endpoints (SPEC-B-010).

GET /api/observability/status   -- system status
GET /api/projects/{id}/events   -- project events
GET /api/projects/{id}/audit    -- LLM audit log
GET /api/projects/{id}/artifacts -- phase artifacts
"""

from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from src.backend.core.observability import Observability

router = APIRouter(prefix="/api", tags=["observability"])


def get_db() -> sqlite3.Connection:  # pragma: no cover -- app wiring
    raise RuntimeError("DB dependency not wired. Override get_db in tests.")


@router.get("/observability/status")
def get_status(db: sqlite3.Connection = Depends(get_db)) -> dict[str, Any]:
    obs = Observability(db)
    status = obs.get_system_status()
    return {"statuses": status, "count": len(status)}


@router.get("/projects/{project_id}/events")
def get_events(
    project_id: str,
    limit: int = Query(100, ge=1, le=1000),
    db: sqlite3.Connection = Depends(get_db),
) -> dict[str, Any]:
    cur = db.execute("SELECT 1 FROM projects WHERE project_id = ?", (project_id,))
    if cur.fetchone() is None:
        raise HTTPException(status_code=404, detail="project not found")

    obs = Observability(db)
    events = obs.get_events(project_id, limit=limit)
    consistency = obs.check_phase_consistency(project_id)
    return {
        "project_id": project_id,
        "events": events,
        "phase_consistency": consistency,
    }


@router.get("/projects/{project_id}/audit")
def get_audit(
    project_id: str,
    limit: int = Query(100, ge=1, le=1000),
    db: sqlite3.Connection = Depends(get_db),
) -> dict[str, Any]:
    cur = db.execute("SELECT 1 FROM projects WHERE project_id = ?", (project_id,))
    if cur.fetchone() is None:
        raise HTTPException(status_code=404, detail="project not found")

    obs = Observability(db)
    audit = obs.get_llm_audit(project_id, limit=limit)
    return {"project_id": project_id, "audit_log": audit, "count": len(audit)}


@router.get("/projects/{project_id}/artifacts")
def get_artifacts(
    project_id: str,
    db: sqlite3.Connection = Depends(get_db),
) -> dict[str, Any]:
    cur = db.execute("SELECT 1 FROM projects WHERE project_id = ?", (project_id,))
    if cur.fetchone() is None:
        raise HTTPException(status_code=404, detail="project not found")

    obs = Observability(db)
    artifacts = obs.get_artifacts(project_id)
    return {"project_id": project_id, "artifacts": artifacts, "count": len(artifacts)}
