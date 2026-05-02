"""Tests for [SPEC-A-006] REST API Route Definitions (25 Endpoints).

Authority: docs/specs/SPEC-A-contracts.md SPEC-1A + SPEC-13A.

The SPEC-1A main route table (v3.15 baseline) lists 25 endpoints:
24 REST (GET/POST/PUT/DELETE) + 1 WS (`/ws/{project_id}`).
The task card AC-1 wording "25 REST endpoints (excluding WS)" is
reconciled against the authoritative spec by asserting 25 total
endpoints with exactly 1 WS and 24 REST.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from src.shared.contracts.api_routes import API_ROUTES, RouteType
from src.shared.schemas.api_requests import (
    AdvanceRequest,
    CreateProjectRequest,
)


class TestAC1Exactly25RestEndpoints:
    """AC-1: Route registry defines exactly 25 endpoints (24 REST + 1 WS)
    with method, path, description."""

    def test_exactly_25_rest_endpoints(self) -> None:
        assert len(API_ROUTES) == 25, (
            f"SPEC-1A main table has 25 rows (24 REST + 1 WS); "
            f"registry has {len(API_ROUTES)}"
        )
        rest = [r for r in API_ROUTES if r["type"] == "rest"]
        ws = [r for r in API_ROUTES if r["type"] == "websocket"]
        assert len(rest) == 24, f"Expected 24 REST endpoints, got {len(rest)}"
        assert len(ws) == 1, f"Expected 1 WS endpoint, got {len(ws)}"

        for route in API_ROUTES:
            assert route["method"], f"Missing method on {route}"
            assert route["path"].startswith(("/api/", "/ws/")), (
                f"Path must start with /api/ or /ws/: {route['path']}"
            )
            assert route["description"], f"Missing description on {route['path']}"


class TestAC2AllRoutesHaveSchemas:
    """AC-2: Each route entry specifies request_schema and response_schema
    references."""

    _NO_BODY_MUTATING = {
        "/api/projects/{id}/tasks/{task_id}/cancel",
        "/api/projects/{id}/skip",
        "/api/settings/preferences/snapshots/{id}/rollback",
    }

    def test_all_routes_have_schemas(self) -> None:
        for route in API_ROUTES:
            assert "request_schema" in route, (
                f"Route {route['path']} missing request_schema key"
            )
            assert "response_schema" in route, (
                f"Route {route['path']} missing response_schema key"
            )
            if (
                route["type"] == "rest"
                and route["method"] in ("POST", "PUT")
                and route["path"] not in self._NO_BODY_MUTATING
            ):
                assert route["request_schema"] is not None, (
                    f"{route['method']} {route['path']} must declare a "
                    f"request_schema (non-empty POST/PUT)"
                )
            assert route["response_schema"] is not None, (
                f"Route {route['path']} must declare a response_schema"
            )


class TestAC3CreateProjectMinDescription:
    """AC-3: POST /api/projects request validates description >= 10 chars."""

    def test_create_project_min_description(self) -> None:
        CreateProjectRequest(title="t", description="0123456789")
        CreateProjectRequest(title="t", description="a full ten plus chars")
        with pytest.raises(ValidationError):
            CreateProjectRequest(title="t", description="123456789")
        with pytest.raises(ValidationError):
            CreateProjectRequest(title="t", description="")


class TestAC4AdvanceRequestSchema:
    """AC-4: POST /api/projects/{id}/advance request includes optional
    confirmed_preferences."""

    def test_advance_request_schema(self) -> None:
        empty = AdvanceRequest()
        assert empty.confirmed_preferences is None
        none_ = AdvanceRequest(confirmed_preferences=None)
        assert none_.confirmed_preferences is None
        filled = AdvanceRequest(
            confirmed_preferences=[{"id": "cand_1", "action": "accept"}]
        )
        assert filled.confirmed_preferences == [{"id": "cand_1", "action": "accept"}]


class TestAC5SkipPhaseConstraint:
    """AC-5: POST /api/projects/{id}/skip is constrained to phase P5/P6 only
    (documented in route metadata)."""

    def test_skip_phase_constraint(self) -> None:
        skip = next(
            (r for r in API_ROUTES if r["path"] == "/api/projects/{id}/skip"),
            None,
        )
        assert skip is not None, "Skip route missing from registry"
        assert skip["method"] == "POST"
        constraints = skip.get("constraints", {})
        assert "allowed_phases" in constraints, (
            "Skip route must declare allowed_phases in constraints"
        )
        assert set(constraints["allowed_phases"]) == {5, 6}, (
            f"Skip allowed_phases must be exactly {{5, 6}} per SPEC-1A; "
            f"got {constraints['allowed_phases']}"
        )


class TestAC6EventsPaginationParams:
    """AC-6: GET /api/projects/{id}/events supports query params limit
    (default 50) and before (cursor)."""

    def test_events_pagination_params(self) -> None:
        events = next(
            (r for r in API_ROUTES if r["path"] == "/api/projects/{id}/events"),
            None,
        )
        assert events is not None, "Events route missing from registry"
        assert events["method"] == "GET"
        params = events.get("query_params", {})
        assert "limit" in params, "events route must declare query param limit"
        assert params["limit"].get("default") == 50, (
            f"events.limit default must be 50; got {params['limit']}"
        )
        assert "before" in params, "events route must declare query param before"
        assert params["before"].get("type") in ("string", "cursor"), (
            f"events.before must be a cursor/string; got {params['before']}"
        )


class TestAC7SnapshotsPaginationParams:
    """AC-7: GET /api/settings/preferences/snapshots supports query param limit
    (default 20)."""

    def test_snapshots_pagination_params(self) -> None:
        snaps = next(
            (
                r
                for r in API_ROUTES
                if r["path"] == "/api/settings/preferences/snapshots"
            ),
            None,
        )
        assert snaps is not None, "Snapshots route missing from registry"
        assert snaps["method"] == "GET"
        params = snaps.get("query_params", {})
        assert "limit" in params, "snapshots route must declare query param limit"
        assert params["limit"].get("default") == 20, (
            f"snapshots.limit default must be 20; got {params['limit']}"
        )


class TestAC8WsEndpointInRegistry:
    """AC-8: WS endpoint `/ws/{project_id}` documented in registry as
    type='websocket'."""

    def test_ws_endpoint_in_registry(self) -> None:
        ws = next((r for r in API_ROUTES if r["path"] == "/ws/{project_id}"), None)
        assert ws is not None, "WS endpoint /ws/{project_id} missing from registry"
        assert ws["type"] == "websocket"
        assert ws["method"] == "WS"
        assert RouteType.WEBSOCKET == "websocket"


class TestAC9MutatingRoutesHaveErrorSchema:
    """AC-9: All POST/PUT/DELETE routes annotated with error_response_schema
    referencing SPEC-13A format."""

    def test_mutating_routes_have_error_schema(self) -> None:
        mutating = [
            r
            for r in API_ROUTES
            if r["type"] == "rest" and r["method"] in ("POST", "PUT", "DELETE")
        ]
        assert mutating, "Expected at least one mutating REST route"
        for route in mutating:
            assert route.get("error_response_schema") == "ErrorResponse", (
                f"{route['method']} {route['path']} must annotate "
                f"error_response_schema='ErrorResponse' (SPEC-13A); "
                f"got {route.get('error_response_schema')}"
            )


class TestAC10RouteRegistryExportFormats:
    """AC-10: Route registry exported as both Python dict and TypeScript const
    for cross-language consumption."""

    def test_route_registry_export_formats(self) -> None:
        assert isinstance(API_ROUTES, tuple), (
            "API_ROUTES must be an immutable tuple of dicts"
        )
        assert all(isinstance(r, dict) for r in API_ROUTES)
        assert len(API_ROUTES) == 25

        repo_root = Path(__file__).resolve().parents[3]
        ts_file = repo_root / "src" / "shared" / "contracts" / "api_routes.ts"
        assert ts_file.is_file(), f"Missing TS registry: {ts_file}"
        ts_text = ts_file.read_text(encoding="utf-8")
        assert "export const API_ROUTES" in ts_text, (
            "TS registry must export `API_ROUTES` const for cross-language use"
        )
        rest_marker = ts_text.count("type: 'rest'") + ts_text.count('type: "rest"')
        ws_marker = ts_text.count("type: 'websocket'") + ts_text.count(
            'type: "websocket"'
        )
        assert rest_marker == 24, (
            f"TS registry must declare 24 rest entries; found {rest_marker}"
        )
        assert ws_marker == 1, (
            f"TS registry must declare 1 websocket entry; found {ws_marker}"
        )
