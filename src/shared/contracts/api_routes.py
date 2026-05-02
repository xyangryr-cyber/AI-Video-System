"""[SPEC-A-006] REST API route registry (SPEC-1A).

Authority: docs/specs/SPEC-A-contracts.md SPEC-1A "API 路由总表".

Exports ``API_ROUTES`` -- an immutable tuple of route metadata dicts covering
every entry in the SPEC-1A v3.15 main table: 24 REST + 1 WebSocket = 25 total.
Downstream code (FastAPI routers, typed frontend clients, OpenAPI
generators) MUST import this registry rather than hard-coding paths.

Each entry has the shape::

    {
        "type": "rest" | "websocket",
        "method": "GET" | "POST" | "PUT" | "DELETE" | "WS",
        "path": "/api/...",
        "description": "...",
        "callers": [...],
        "request_schema": "<ClassName>" | None,     # Pydantic class in api_requests.py
        "response_schema": "<ClassName>",           # Pydantic class in api_responses.py
        "error_response_schema": "ErrorResponse" | None,  # SPEC-13A; set on all
                                                            # rest POST/PUT/DELETE
        "constraints": {...},                       # phase gates, etc.
        "query_params": {...},                      # for GET with pagination
    }
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class RouteType(str, Enum):
    REST = "rest"
    WEBSOCKET = "websocket"


_ERR = "ErrorResponse"


API_ROUTES: tuple[dict[str, Any], ...] = (
    # --- Projects: list / CRUD -------------------------------------------
    {
        "type": RouteType.REST.value,
        "method": "GET",
        "path": "/api/projects",
        "description": "List projects (paginated in V1.5).",
        "callers": ["frontend: project-list"],
        "request_schema": None,
        "response_schema": "ProjectListResponse",
        "error_response_schema": None,
        "constraints": {},
        "query_params": {},
    },
    {
        "type": RouteType.REST.value,
        "method": "POST",
        "path": "/api/projects",
        "description": "Create project; description must be >= 10 characters.",
        "callers": ["frontend: new-project-wizard"],
        "request_schema": "CreateProjectRequest",
        "response_schema": "CreateProjectResponse",
        "error_response_schema": _ERR,
        "constraints": {"description_min_chars": 10},
        "query_params": {},
    },
    {
        "type": RouteType.REST.value,
        "method": "GET",
        "path": "/api/projects/{id}",
        "description": "Project detail.",
        "callers": ["frontend: project-detail"],
        "request_schema": None,
        "response_schema": "ProjectInfo",
        "error_response_schema": None,
        "constraints": {},
        "query_params": {},
    },
    {
        "type": RouteType.REST.value,
        "method": "DELETE",
        "path": "/api/projects/{id}",
        "description": "Soft-delete project.",
        "callers": ["frontend: project-list"],
        "request_schema": None,
        "response_schema": "OkResponse",
        "error_response_schema": _ERR,
        "constraints": {"soft_delete": True},
        "query_params": {},
    },
    # --- Projects: workflow FSM ------------------------------------------
    {
        "type": RouteType.REST.value,
        "method": "GET",
        "path": "/api/projects/{id}/state",
        "description": "Full ProjectState for frontend state restoration.",
        "callers": ["frontend: workflow-page"],
        "request_schema": None,
        "response_schema": "ProjectState",
        "error_response_schema": None,
        "constraints": {},
        "query_params": {},
    },
    {
        "type": RouteType.REST.value,
        "method": "POST",
        "path": "/api/projects/{id}/advance",
        "description": "Advance to next phase (idempotent; see SPEC-3.7).",
        "callers": ["frontend: advance-button"],
        "request_schema": "AdvanceRequest",
        "response_schema": "AdvanceResponse",
        "error_response_schema": _ERR,
        "constraints": {"idempotent": True},
        "query_params": {},
    },
    {
        "type": RouteType.REST.value,
        "method": "POST",
        "path": "/api/projects/{id}/skip",
        "description": "Skip current phase (P5/P6 only per SPEC-1A).",
        "callers": ["frontend: skip-button"],
        "request_schema": None,
        "response_schema": "SkipResponse",
        "error_response_schema": _ERR,
        "constraints": {"allowed_phases": [5, 6]},
        "query_params": {},
    },
    {
        "type": RouteType.REST.value,
        "method": "POST",
        "path": "/api/projects/{id}/rollback",
        "description": "Roll back to a target phase; invalidates downstream.",
        "callers": ["frontend: rollback-action"],
        "request_schema": "RollbackRequest",
        "response_schema": "RollbackResponse",
        "error_response_schema": _ERR,
        "constraints": {},
        "query_params": {},
    },
    {
        "type": RouteType.REST.value,
        "method": "POST",
        "path": "/api/projects/{id}/chat",
        "description": "Send conversation message (routed by IntentRouter).",
        "callers": ["frontend: chat-input"],
        "request_schema": "ChatRequest",
        "response_schema": "ChatResponse",
        "error_response_schema": _ERR,
        "constraints": {"routed_by": "IntentRouter"},
        "query_params": {},
    },
    # --- Projects: tasks --------------------------------------------------
    {
        "type": RouteType.REST.value,
        "method": "GET",
        "path": "/api/projects/{id}/tasks",
        "description": "Task ledger list for the project.",
        "callers": ["frontend: task-panel"],
        "request_schema": None,
        "response_schema": "TaskListResponse",
        "error_response_schema": None,
        "constraints": {},
        "query_params": {},
    },
    {
        "type": RouteType.REST.value,
        "method": "POST",
        "path": "/api/projects/{id}/tasks/{task_id}/cancel",
        "description": "Cancel a task (pending/queued states only).",
        "callers": ["frontend: task-panel"],
        "request_schema": None,
        "response_schema": "OkResponse",
        "error_response_schema": _ERR,
        "constraints": {"cancellable_states": ["pending", "queued"]},
        "query_params": {},
    },
    # --- Projects: preferences & artifacts --------------------------------
    {
        "type": RouteType.REST.value,
        "method": "GET",
        "path": "/api/projects/{id}/preferences",
        "description": "Get per-project preferences payload.",
        "callers": ["frontend: preferences-confirm-ui"],
        "request_schema": None,
        "response_schema": "Preferences",
        "error_response_schema": None,
        "constraints": {},
        "query_params": {},
    },
    {
        "type": RouteType.REST.value,
        "method": "POST",
        "path": "/api/projects/{id}/preferences/confirm",
        "description": "Confirm candidate preference decisions.",
        "callers": ["frontend: candidate-selector"],
        "request_schema": "PreferencesConfirmRequest",
        "response_schema": "PreferencesConfirmResponse",
        "error_response_schema": _ERR,
        "constraints": {},
        "query_params": {},
    },
    {
        "type": RouteType.REST.value,
        "method": "GET",
        "path": "/api/projects/{id}/phases/{phase}/artifact",
        "description": "Fetch phase artifact payload (JSON or file URL).",
        "callers": ["frontend: preview-component", "render: theme-config"],
        "request_schema": None,
        "response_schema": "ArtifactEnvelope",
        "error_response_schema": None,
        "constraints": {},
        "query_params": {},
    },
    # --- Projects: events & costs ----------------------------------------
    {
        "type": RouteType.REST.value,
        "method": "GET",
        "path": "/api/projects/{id}/events",
        "description": "Historical event list; paginated via limit + cursor.",
        "callers": ["frontend: agent-activity-panel"],
        "request_schema": None,
        "response_schema": "EventsResponse",
        "error_response_schema": None,
        "constraints": {},
        "query_params": {
            "limit": {"type": "integer", "default": 50},
            "before": {"type": "cursor", "default": None},
        },
    },
    {
        "type": RouteType.REST.value,
        "method": "GET",
        "path": "/api/projects/{id}/costs",
        "description": "Project-level cost breakdown (total + by phase).",
        "callers": ["frontend: cost-panel"],
        "request_schema": None,
        "response_schema": "CostsResponse",
        "error_response_schema": None,
        "constraints": {},
        "query_params": {},
    },
    # --- System -----------------------------------------------------------
    {
        "type": RouteType.REST.value,
        "method": "GET",
        "path": "/api/system/status",
        "description": "Pre-flight system status and degraded services list.",
        "callers": ["frontend: system-banner"],
        "request_schema": None,
        "response_schema": "SystemStatus",
        "error_response_schema": None,
        "constraints": {},
        "query_params": {},
    },
    # --- Settings ---------------------------------------------------------
    {
        "type": RouteType.REST.value,
        "method": "GET",
        "path": "/api/settings",
        "description": "Fetch global settings (model_config + brand_kit).",
        "callers": ["frontend: settings-page"],
        "request_schema": None,
        "response_schema": "SettingsResponse",
        "error_response_schema": None,
        "constraints": {},
        "query_params": {},
    },
    {
        "type": RouteType.REST.value,
        "method": "PUT",
        "path": "/api/settings/model-config",
        "description": "Update global model configuration.",
        "callers": ["frontend: settings-page"],
        "request_schema": "ModelConfig",
        "response_schema": "OkResponse",
        "error_response_schema": _ERR,
        "constraints": {},
        "query_params": {},
    },
    {
        "type": RouteType.REST.value,
        "method": "PUT",
        "path": "/api/settings/brand-kit",
        "description": "Update brand kit (SQLite-only; no file writes).",
        "callers": ["frontend: settings-page"],
        "request_schema": "BrandKit",
        "response_schema": "OkResponse",
        "error_response_schema": _ERR,
        "constraints": {"no_file_writes": True},
        "query_params": {},
    },
    {
        "type": RouteType.REST.value,
        "method": "GET",
        "path": "/api/settings/preferences",
        "description": "Fetch global user preferences markdown.",
        "callers": ["frontend: settings-page"],
        "request_schema": None,
        "response_schema": "PreferencesResponse",
        "error_response_schema": None,
        "constraints": {},
        "query_params": {},
    },
    {
        "type": RouteType.REST.value,
        "method": "PUT",
        "path": "/api/settings/preferences",
        "description": "Update global preferences; auto-creates snapshot.",
        "callers": ["frontend: settings-page"],
        "request_schema": "PreferencesUpdateRequest",
        "response_schema": "PreferencesUpdateResponse",
        "error_response_schema": _ERR,
        "constraints": {"auto_snapshot": True},
        "query_params": {},
    },
    {
        "type": RouteType.REST.value,
        "method": "GET",
        "path": "/api/settings/preferences/snapshots",
        "description": "List preference snapshots (paginated via limit).",
        "callers": ["frontend: settings-page"],
        "request_schema": None,
        "response_schema": "SnapshotListResponse",
        "error_response_schema": None,
        "constraints": {},
        "query_params": {
            "limit": {"type": "integer", "default": 20},
        },
    },
    {
        "type": RouteType.REST.value,
        "method": "POST",
        "path": "/api/settings/preferences/snapshots/{id}/rollback",
        "description": "Roll preferences back to a chosen snapshot.",
        "callers": ["frontend: settings-page"],
        "request_schema": None,
        "response_schema": "SnapshotRollbackResponse",
        "error_response_schema": _ERR,
        "constraints": {},
        "query_params": {},
    },
    # --- WebSocket --------------------------------------------------------
    {
        "type": RouteType.WEBSOCKET.value,
        "method": "WS",
        "path": "/ws/{project_id}",
        "description": "Real-time event stream per SPEC-11A envelope.",
        "callers": ["frontend: workflow-page ws"],
        "request_schema": None,
        "response_schema": "WsEventEnvelope",
        "error_response_schema": None,
        "constraints": {},
        "query_params": {},
    },
)


__all__ = ["API_ROUTES", "RouteType"]
