"""FastAPI application entrypoint.

[SPEC-B-001] Three-service topology: web (Vite) / api (FastAPI) / worker (Huey).
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.backend.api.middleware.error_handler import register_error_handlers
from src.backend.api.routes import cost, observability, preferences, projects, settings_bridge, system, tasks, websocket
from src.backend.db.connection import create_connection


@asynccontextmanager
async def lifespan(application: FastAPI):
    # startup
    import os as _os
    from pathlib import Path as _Path
    from src.backend.db.migration_runner import run_migrations
    from src.backend.core.preflight import run_full_preflight

    application.state.db_connection = create_connection()

    # Run database migrations before anything touches the schema
    _migrations_dir = _Path("src/backend/db/migrations")
    run_migrations(application.state.db_connection, _migrations_dir)

    def _get_db_override():
        return application.state.db_connection

    application.dependency_overrides[projects.get_db] = _get_db_override
    application.dependency_overrides[system.get_db] = _get_db_override
    application.dependency_overrides[observability.get_db] = _get_db_override
    application.dependency_overrides[preferences.get_db] = _get_db_override
    application.dependency_overrides[cost.get_db] = _get_db_override
    application.dependency_overrides[tasks.get_db] = _get_db_override

    # Run preflight checks after migrations and DI wiring
    run_full_preflight(application.state.db_connection)

    yield

    # shutdown
    application.state.db_connection.close()


app = FastAPI(title="AI Video System", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# JSON Lines request logging
# ---------------------------------------------------------------------------
class JsonLineFormatter(logging.Formatter):
    """Log every request as a JSON Lines record."""

    def format(self, record: logging.LogRecord) -> str:
        import json

        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        entry: dict[str, object] = {
            "ts": ts,
            "level": record.levelname,
            "service": "api",
            "event": record.msg,
        }
        for attr in ("method", "path", "status_code", "duration_ms", "project_id"):
            val = getattr(record, attr, None)
            if val is not None:
                entry[attr] = val
        return json.dumps(entry, default=str)


_log_handler = logging.StreamHandler()
_log_handler.setFormatter(JsonLineFormatter())
_log_handler.setLevel(logging.INFO)
logging.getLogger("uvicorn.access").addHandler(_log_handler)
logging.getLogger("uvicorn.access").setLevel(logging.INFO)


@app.middleware("http")
async def json_request_log_middleware(request, call_next):
    import time

    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000)
    logger = logging.getLogger("uvicorn.access")
    logger.info(
        "request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response


register_error_handlers(app)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(system.router)
app.include_router(tasks.router)
app.include_router(preferences.router)
app.include_router(observability.router)
app.include_router(cost.router)
app.include_router(settings_bridge.router)
app.include_router(websocket.router)
app.include_router(projects.router)
