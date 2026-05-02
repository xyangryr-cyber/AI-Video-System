"""Tests for [SPEC-A-006] REST API Route Definitions (25 Endpoints)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from src.shared.contracts.api_routes import API_ROUTES, RouteType
from src.shared.schemas.api_requests import AdvanceRequest, CreateProjectRequest


class TestAC1Exactly25RestEndpoints:
    """AC-1: Route registry defines exactly 25 REST endpoints (excluding WS) with method, path, description"""

    def test_exactly_25_rest_endpoints(self):
        assert len(API_ROUTES) == 25
        rest = [r for r in API_ROUTES if r["type"] == "rest"]
        ws = [r for r in API_ROUTES if r["type"] == "websocket"]
        assert len(rest) == 24
        assert len(ws) == 1

        for route in API_ROUTES:
            assert route["method"]
            assert route["path"].startswith(("/api/", "/ws/"))
            assert route["description"]


class TestAC2AllRoutesHaveSchemas:
    """AC-2: Each route entry specifies request_schema and response_schema references"""

    _NO_BODY_MUTATING = {
        "/api/projects/{id}/tasks/{task_id}/cancel",
        "/api/projects/{id}/skip",
        "/api/settings/preferences/snapshots/{id}/rollback",
    }

    def test_all_routes_have_schemas(self):
        for route in API_ROUTES:
            assert "request_schema" in route
            assert "response_schema" in route
            if (
                route["type"] == "rest"
                and route["method"] in ("POST", "PUT")
                and route["path"] not in self._NO_BODY_MUTATING
            ):
                assert route["request_schema"] is not None
            assert route["response_schema"] is not None


class TestAC3CreateProjectMinDescription:
    """AC-3: POST /api/projects request validates description >= 10 chars"""

    def test_create_project_min_description(self):
        CreateProjectRequest(title="t", description="0123456789")
        CreateProjectRequest(title="t", description="a full ten plus chars")
        with pytest.raises(ValidationError):
            CreateProjectRequest(title="t", description="123456789")
        with pytest.raises(ValidationError):
            CreateProjectRequest(title="t", description="")


class TestAC4AdvanceRequestSchema:
    """AC-4: POST /api/projects/{id}/advance request includes optional confirmed_preferences"""

    def test_advance_request_schema(self):
        empty = AdvanceRequest()
        assert empty.confirmed_preferences is None
        filled = AdvanceRequest(
            confirmed_preferences=[{"id": "cand_1", "action": "accept"}]
        )
        assert filled.confirmed_preferences == [{"id": "cand_1", "action": "accept"}]


class TestAC5SkipPhaseConstraint:
    """AC-5: POST /api/projects/{id}/skip is constrained to phase P5/P6 only (documented in route metadata)"""

    def test_skip_phase_constraint(self):
        skip = next(
            (r for r in API_ROUTES if r["path"] == "/api/projects/{id}/skip"), None
        )
        assert skip is not None
        assert skip["method"] == "POST"
        constraints = skip.get("constraints", {})
        assert "allowed_phases" in constraints
        assert set(constraints["allowed_phases"]) == {5, 6}


class TestAC6EventsPaginationParams:
    """AC-6: GET /api/projects/{id}/events supports query params limit (default 50) and before (cursor)"""

    def test_events_pagination_params(self):
        events = next(
            (r for r in API_ROUTES if r["path"] == "/api/projects/{id}/events"), None
        )
        assert events is not None
        assert events["method"] == "GET"
        params = events.get("query_params", {})
        assert "limit" in params
        assert params["limit"].get("default") == 50
        assert "before" in params
        assert params["before"].get("type") in ("string", "cursor")


class TestAC7SnapshotsPaginationParams:
    """AC-7: GET /api/settings/preferences/snapshots supports query param limit (default 20)"""

    def test_snapshots_pagination_params(self):
        snaps = next(
            (
                r
                for r in API_ROUTES
                if r["path"] == "/api/settings/preferences/snapshots"
            ),
            None,
        )
        assert snaps is not None
        assert snaps["method"] == "GET"
        params = snaps.get("query_params", {})
        assert "limit" in params
        assert params["limit"].get("default") == 20


class TestAC8WsEndpointInRegistry:
    """AC-8: WS endpoint `/ws/{project_id}` documented in registry as type='websocket'"""

    def test_ws_endpoint_in_registry(self):
        ws = next((r for r in API_ROUTES if r["path"] == "/ws/{project_id}"), None)
        assert ws is not None
        assert ws["type"] == "websocket"
        assert ws["method"] == "WS"
        assert RouteType.WEBSOCKET == "websocket"


class TestAC9MutatingRoutesHaveErrorSchema:
    """AC-9: All POST/PUT/DELETE routes annotated with error_response_schema referencing SPEC-13A format"""

    def test_mutating_routes_have_error_schema(self):
        mutating = [
            r
            for r in API_ROUTES
            if r["type"] == "rest" and r["method"] in ("POST", "PUT", "DELETE")
        ]
        assert mutating
        for route in mutating:
            assert route.get("error_response_schema") == "ErrorResponse"


class TestAC10RouteRegistryExportFormats:
    """AC-10: Route registry exported as both Python dict and TypeScript const for cross-language consumption"""

    def test_route_registry_export_formats(self):
        assert isinstance(API_ROUTES, tuple)
        assert all(isinstance(r, dict) for r in API_ROUTES)
        assert len(API_ROUTES) == 25

        repo_root = Path(__file__).resolve().parents[3]
        ts_file = repo_root / "src" / "shared" / "contracts" / "api_routes.ts"
        assert ts_file.is_file()
        ts_text = ts_file.read_text(encoding="utf-8")
        assert "export const API_ROUTES" in ts_text
        rest_marker = ts_text.count("type: 'rest'") + ts_text.count('type: "rest"')
        ws_marker = ts_text.count("type: 'websocket'") + ts_text.count(
            'type: "websocket"'
        )
        assert rest_marker == 24
        assert ws_marker == 1
