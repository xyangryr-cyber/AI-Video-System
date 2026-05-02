"""SPEC-B-009 FastAPI startup hook.

Registers a lifespan handler that fires ``run_full_preflight`` against
the app's SQLite connection when the API boots (SPEC-1.3, AC-6). Split
into its own module so tests can exercise startup in isolation with an
in-memory DB, and production ``main`` wiring can drop in a real
``conn_provider`` without pulling in the rest of the ``api`` surface.
"""

from __future__ import annotations

import sqlite3
from typing import Any
from contextlib import asynccontextmanager
from typing import Callable, Dict, Optional

from fastapi import FastAPI

from src.backend.core.preflight import Runner, run_full_preflight


def register_preflight_startup(
    app: FastAPI,
    conn_provider: Callable[[], sqlite3.Connection],
    runners: Optional[Dict[str, Runner]] = None,
) -> None:
    """Attach a Pre-flight sweep to the FastAPI lifespan startup phase.

    ``conn_provider`` is called once at startup. Tests pass a lambda
    returning a pre-seeded in-memory connection; production passes the
    app's singleton SQLite connection factory.
    """

    existing = app.router.lifespan_context

    @asynccontextmanager
    async def _lifespan(fastapi_app: FastAPI) -> Any:
        conn = conn_provider()
        run_full_preflight(conn, runners=runners)
        async with existing(fastapi_app):
            yield

    app.router.lifespan_context = _lifespan
