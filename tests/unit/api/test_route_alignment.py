"""[SPEC-GAPFIX-013] Route alignment tests — check no missing, no extra, no double-prefix."""

from __future__ import annotations

import re

from src.backend.api.main import app
from src.shared.contracts.api_routes import API_ROUTES


def norm(p: str) -> str:
    """Normalise path parameters to ``{}`` for comparison."""
    return re.sub(r"\{[^}]+\}", "{}", p)


_BUILTIN_PREFIXES = ("/docs", "/openapi.json", "/redoc")


def _actual_routes():
    """Return set of ``(method, normalised_path)`` for all REST routes."""
    actual = set()
    for r in app.routes:
        if not hasattr(r, "methods"):
            continue
        for m in r.methods:
            if m in {"HEAD", "OPTIONS"}:
                continue
            np = norm(r.path)
            # Exclude FastAPI built-in docs/redoc/OpenAPI paths.
            if np.startswith(_BUILTIN_PREFIXES):
                continue
            actual.add((m, np))
    return actual


def _expected_routes():
    """Return set of ``(method, normalised_path)`` from SPEC-1A."""
    return {
        (r["method"], norm(r["path"]))
        for r in API_ROUTES
        if r["type"] == "rest"
    }


def test_no_missing_routes():
    """Every SPEC-1A route must exist in the app."""
    expected = _expected_routes()
    actual = _actual_routes()
    missing = expected - actual
    assert len(missing) == 0, f"MISSING routes (SPEC-1A routes not in app): {sorted(missing)}"


def test_no_extra_routes():
    """No route should exist that is not in SPEC-1A (plus known intentional extras)."""
    expected = _expected_routes()
    # Allow /health which is not a SPEC-1A route
    expected.add(("GET", "/health"))
    # Known intentional extras from observability router (monitoring endpoints)
    expected |= {
        ("GET", "/api/observability/status"),
        ("GET", "/api/projects/{}/audit"),
        ("GET", "/api/projects/{}/artifacts"),
        # GAPFIX-041: frontend-required routes not yet in SPEC-1A contract
        ("POST", "/api/projects/{}/materials/supplement"),
        ("GET", "/api/projects/{}/preferences/writeback-suggestions"),
        ("POST", "/api/projects/{}/preferences/stage"),
    }
    actual = _actual_routes()
    extra = actual - expected
    assert len(extra) == 0, f"EXTRA routes (in app but not in SPEC-1A): {sorted(extra)}"


def test_no_double_prefix_routes():
    """No route path should contain /api/ after the first 5 characters."""
    actual = _actual_routes()
    double = [p for _, p in actual if "/api/" in p[5:]]
    assert len(double) == 0, f"DOUBLE-PREFIX routes: {double}"
