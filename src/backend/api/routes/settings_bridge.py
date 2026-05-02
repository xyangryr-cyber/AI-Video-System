"""[BRIDGE] Settings API router -- serves model config and brand kit to frontend."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/api/settings", tags=["settings"])

MODEL_CONFIG_PATH = Path("config/model_config.json")


def _get_db() -> sqlite3.Connection:
    import os

    db_raw = os.environ.get("DATABASE_URL", "sqlite:///data/db/dev.sqlite3")
    db_path = Path(db_raw.removeprefix("sqlite:///"))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_settings_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.commit()


@router.get("")
def get_settings() -> dict[str, Any]:
    # Read model_config from file
    try:
        model_config_data = json.loads(MODEL_CONFIG_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        model_config_data = {}

    # Read brand_kit from DB
    conn = _get_db()
    try:
        _ensure_settings_table(conn)
        row = conn.execute("SELECT value FROM settings WHERE key = 'brand_kit'").fetchone()
        brand_kit = (
            json.loads(row["value"])
            if row
            else {
                "primary_color": "#1a1a2e",
                "accent_color": "#e94560",
                "font_family": "Inter",
            }
        )
    finally:
        conn.close()

    return {
        "model_config_data": model_config_data,
        "brand_kit": brand_kit,
    }


@router.put("/model-config")
def update_model_config(body: dict[str, Any]) -> dict[str, Any]:
    try:
        MODEL_CONFIG_PATH.write_text(
            json.dumps(body, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except OSError as exc:
        return {"ok": False, "error": str(exc)}
    return {"ok": True}


@router.get("/preferences")
def get_preferences() -> dict[str, Any]:
    conn = _get_db()
    try:
        _ensure_settings_table(conn)
        row = conn.execute("SELECT value FROM settings WHERE key = 'preferences'").fetchone()
        prefs = json.loads(row["value"]) if row else {}
    finally:
        conn.close()
    return {"preferences": prefs}


@router.put("/preferences")
def update_preferences(body: dict[str, Any]) -> dict[str, Any]:
    import datetime
    import uuid

    conn = _get_db()
    try:
        _ensure_settings_table(conn)
        now = datetime.datetime.utcnow().isoformat() + "Z"
        snapshot_id = f"snap_{uuid.uuid4().hex[:8]}"
        # Save old value as snapshot
        old = conn.execute("SELECT value FROM settings WHERE key = 'preferences'").fetchone()
        if old:
            snaps = conn.execute(
                "SELECT value FROM settings WHERE key = 'preferences_snapshots'"
            ).fetchone()
            snapshots = json.loads(snaps["value"]) if snaps else []
            snapshots.append(
                {"id": snapshot_id, "data": json.loads(old["value"]), "created_at": now}
            )
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                ["preferences_snapshots", json.dumps(snapshots), now],
            )
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
            ["preferences", json.dumps(body), now],
        )
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "snapshot_id": snapshot_id}


@router.put("/brand-kit")
def update_brand_kit(body: dict[str, Any]) -> dict[str, Any]:
    import datetime

    conn = _get_db()
    try:
        _ensure_settings_table(conn)
        now = datetime.datetime.utcnow().isoformat() + "Z"
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
            ["brand_kit", json.dumps(body), now],
        )
        conn.commit()
    finally:
        conn.close()
    return {"ok": True}


@router.get("/preferences/snapshots")
def list_preference_snapshots() -> dict[str, Any]:
    conn = _get_db()
    try:
        _ensure_settings_table(conn)
        row = conn.execute(
            "SELECT value FROM settings WHERE key = 'preferences_snapshots'"
        ).fetchone()
        snapshots = json.loads(row["value"]) if row else []
    finally:
        conn.close()
    return {"snapshots": snapshots}


@router.post("/preferences/snapshots/{snapshot_id}/rollback")
def rollback_preferences(snapshot_id: str) -> dict[str, Any]:
    import datetime

    conn = _get_db()
    try:
        _ensure_settings_table(conn)
        row = conn.execute(
            "SELECT value FROM settings WHERE key = 'preferences_snapshots'"
        ).fetchone()
        snapshots = json.loads(row["value"]) if row else []
        target = next((s for s in snapshots if s["id"] == snapshot_id), None)
        if not target:
            return {"ok": False, "error": "Snapshot not found"}
        now = datetime.datetime.utcnow().isoformat() + "Z"
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
            ["preferences", json.dumps(target["data"]), now],
        )
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "new_snapshot_id": snapshot_id}
