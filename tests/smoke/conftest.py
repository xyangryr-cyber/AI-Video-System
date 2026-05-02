"""[SPEC-GAPFIX-043] Smoke test fixtures and helpers."""

from __future__ import annotations

import os

import pytest


def is_backend_running() -> bool:
    """Check if FastAPI backend is reachable."""
    import urllib.request

    try:
        resp = urllib.request.urlopen("http://localhost:8000/health", timeout=2)
        return resp.status == 200
    except Exception:
        return False


def is_frontend_running() -> bool:
    """Check if Vite frontend is reachable."""
    import urllib.request

    try:
        resp = urllib.request.urlopen("http://localhost:3000", timeout=2)
        return resp.status == 200
    except Exception:
        return False


needs_backend = pytest.mark.skipif(
    not is_backend_running(),
    reason="Backend not running on localhost:8000",
)

needs_frontend = pytest.mark.skipif(
    not is_frontend_running(),
    reason="Frontend not running on localhost:3000",
)
