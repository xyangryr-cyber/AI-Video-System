"""Phase 0 US1 API contract tests.

These tests validate that API request/response schemas match the contracts
defined in specs/001-phase-0-requirements/contracts/rest-api.md.

The backend MAY NOT yet serve the exact contract response format — that is the
expected TDD RED state. These tests define the target contract shapes.
"""

from __future__ import annotations

import json
import time
from datetime import datetime

import httpx
import pytest

BASE_URL = "http://localhost:8000/api"

pytestmark = pytest.mark.contract


# ---- helpers -----------------------------------------------------------


def _parse_iso8601(s: str) -> datetime:
    """Parse an ISO 8601 timestamp string (accepts Z or +00:00 suffix)."""
    normalized = s.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _create_project(client: httpx.Client, title: str, description: str) -> dict:
    """Create a project and return the parsed JSON response body."""
    resp = client.post(
        f"{BASE_URL}/projects",
        json={"title": title, "description": description},
    )
    return resp.json()


# ---- T007: POST /api/projects ------------------------------------------


class TestCreateProjectContract:
    """Contract tests for POST /api/projects (rest-api.md section 1)."""

    def test_create_project_returns_201_with_correct_schema(self):
        """POST /api/projects with valid payload returns 201 and contract shape."""
        payload = {
            "title": "Test Video",
            "description": "A test description for video creation that is long enough",
        }
        with httpx.Client(timeout=httpx.Timeout(30.0)) as client:
            resp = client.post(f"{BASE_URL}/projects", json=payload)

        # Status code must be 201 per contract
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"

        body = resp.json()

        # Required top-level fields per contract
        assert "project_id" in body, f"Missing project_id in {json.dumps(body)}"
        assert body["project_id"].startswith(
            "proj_"
        ), f"project_id must start with 'proj_': {body['project_id']}"
        assert body.get("title") == payload["title"]
        assert body.get("description") == payload["description"]
        assert (
            body.get("current_phase") == 0
        ), f"current_phase must be 0, got {body.get('current_phase')}"
        assert body.get("status") == "active", f"status must be 'active', got {body.get('status')}"
        assert body.get("latest_reached_phase") == 0
        assert isinstance(body.get("phase_history"), list), "phase_history must be a list"

        # Timestamp fields must be valid ISO 8601
        created = body.get("created_at")
        assert created is not None, "created_at is required"
        _parse_iso8601(created)

        updated = body.get("updated_at")
        assert updated is not None, "updated_at is required"
        _parse_iso8601(updated)

    def test_create_project_empty_title_returns_400(self):
        """POST /api/projects with empty title returns 400 VALIDATION_ERROR."""
        payload = {"title": "", "description": "A test description long enough"}
        with httpx.Client(timeout=httpx.Timeout(30.0)) as client:
            resp = client.post(f"{BASE_URL}/projects", json=payload)

        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"

        body = resp.json()
        # Contract error shape: {"error": {"code": "VALIDATION_ERROR", "message": ...}}
        assert "error" in body, f"Expected error envelope, got {json.dumps(body)}"
        error = body["error"]
        assert (
            error.get("code") == "VALIDATION_ERROR"
        ), f"Expected VALIDATION_ERROR, got {error.get('code')}"
        # Message should reference title/empty in Chinese
        msg = error.get("message", "")
        assert msg, "Error message is required"

    def test_create_project_short_description_returns_400(self):
        """POST /api/projects with description < 10 chars returns 400 VALIDATION_ERROR."""
        payload = {"title": "Test", "description": "short"}
        with httpx.Client(timeout=httpx.Timeout(30.0)) as client:
            resp = client.post(f"{BASE_URL}/projects", json=payload)

        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"

        body = resp.json()
        assert "error" in body, f"Expected error envelope, got {json.dumps(body)}"
        error = body["error"]
        assert (
            error.get("code") == "VALIDATION_ERROR"
        ), f"Expected VALIDATION_ERROR, got {error.get('code')}"


# ---- T008: GET /api/projects/{id}/state ---------------------------------


class TestGetProjectStateContract:
    """Contract tests for GET /api/projects/{id}/state (rest-api.md section 2)."""

    def test_get_state_returns_200_with_correct_schema(self):
        """GET /projects/{id}/state returns 200 with project, phases, system_status."""
        with httpx.Client(timeout=httpx.Timeout(30.0)) as client:
            # Create a project first
            created = _create_project(
                client,
                "State Contract Test",
                "A description that is long enough for state contract validation",
            )

            # Extract the project_id
            project_id = created.get("project_id") or created.get("id")
            assert project_id, f"Cannot extract project_id from: {json.dumps(created)}"

            resp = client.get(f"{BASE_URL}/projects/{project_id}/state")

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

        body = resp.json()

        # Top-level sections per contract
        assert "project" in body, f"Missing 'project' section in {json.dumps(body)}"
        assert "phases" in body, f"Missing 'phases' section in {json.dumps(body)}"
        assert "system_status" in body, f"Missing 'system_status' section in {json.dumps(body)}"

        # project section required fields
        project = body["project"]
        assert project.get("project_id") == project_id
        assert "title" in project
        assert "description" in project
        assert "current_phase" in project
        assert "status" in project

        # phases section: must be a list with at least phase 0
        phases = body["phases"]
        assert isinstance(phases, list), f"phases must be a list, got {type(phases)}"
        assert len(phases) > 0, "phases list must not be empty"
        phase_nums = [p.get("phase_num") for p in phases]
        assert 0 in phase_nums, f"phase 0 must be present in phases, got {phase_nums}"

        # system_status section
        system_status = body["system_status"]
        assert (
            "llm_available" in system_status
        ), f"system_status must have llm_available: {json.dumps(system_status)}"
        assert isinstance(system_status["llm_available"], bool), "llm_available must be boolean"

    def test_get_state_nonexistent_project_returns_404(self):
        """GET /projects/{nonexistent_id}/state returns 404 NOT_FOUND."""
        with httpx.Client(timeout=httpx.Timeout(30.0)) as client:
            resp = client.get(f"{BASE_URL}/projects/nonexistent_id/state")

        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"

        body = resp.json()
        assert "error" in body, f"Expected error envelope, got {json.dumps(body)}"
        error = body["error"]
        assert error.get("code") == "NOT_FOUND", f"Expected NOT_FOUND, got {error.get('code')}"


# ---- T009: GET /api/projects/{id}/phases/0/artifact --------------------


class TestGetPhaseArtifactContract:
    """Contract tests for GET /api/projects/{id}/phases/0/artifact (rest-api.md section 3)."""

    def test_get_artifact_returns_200_with_requirements_schema(self):
        """GET /projects/{id}/phases/0/artifact returns 200 with requirements.json shape.

        Polls with retry (up to 30s, 2s intervals) because the artifact is
        generated by an async background task.
        """
        with httpx.Client(timeout=httpx.Timeout(60.0)) as client:
            # Create a project
            created = _create_project(
                client,
                "Artifact Contract Test",
                "A description long enough for artifact generation test validation",
            )
            project_id = created.get("project_id") or created.get("id")
            assert project_id, f"Cannot extract project_id from: {json.dumps(created)}"

            # Poll until artifact is generated or timeout
            artifact_url = f"{BASE_URL}/projects/{project_id}/phases/0/artifact"
            deadline = time.time() + 30.0
            last_resp = None

            while time.time() < deadline:
                resp = client.get(artifact_url)
                if resp.status_code == 200:
                    last_resp = resp
                    break
                if resp.status_code != 404:
                    # Unexpected status, record and break to surface in assertion
                    last_resp = resp
                    break
                time.sleep(2.0)
            else:
                # Timed out; use the last 404 response to surface the contract gap
                assert last_resp is not None, "No response received during polling"
                pytest.fail(
                    f"Artifact not generated within 30s. "
                    f"Last response ({last_resp.status_code}): {last_resp.text}"
                )

        assert last_resp is not None
        assert (
            last_resp.status_code == 200
        ), f"Expected 200, got {last_resp.status_code}: {last_resp.text}"

        body = last_resp.json()

        # Required fields per contract section 3
        assert "project_id" in body, f"Missing project_id in {json.dumps(body)}"
        assert body["project_id"] == project_id

        assert "title" in body, f"Missing title in {json.dumps(body)}"

        assert "topic" in body, f"Missing topic in {json.dumps(body)}"
        assert len(body.get("topic", "")) >= 5, f"topic must be >= 5 chars: {body.get('topic')}"

        # target_duration
        assert "target_duration" in body, f"Missing target_duration in {json.dumps(body)}"
        td = body["target_duration"]
        assert isinstance(td, dict), f"target_duration must be dict, got {type(td)}"
        assert "min_sec" in td, f"target_duration missing min_sec: {td}"
        assert "max_sec" in td, f"target_duration missing max_sec: {td}"
        assert isinstance(
            td.get("min_sec"), (int, float)
        ), f"min_sec must be numeric: {td.get('min_sec')}"
        assert isinstance(
            td.get("max_sec"), (int, float)
        ), f"max_sec must be numeric: {td.get('max_sec')}"

        # target_word_count
        assert "target_word_count" in body, f"Missing target_word_count in {json.dumps(body)}"
        twc = body["target_word_count"]
        assert isinstance(twc, dict), f"target_word_count must be dict, got {type(twc)}"
        assert "min" in twc, f"target_word_count missing min: {twc}"
        assert "max" in twc, f"target_word_count missing max: {twc}"
        assert isinstance(twc.get("min"), (int, float)), f"min must be numeric: {twc.get('min')}"
        assert isinstance(twc.get("max"), (int, float)), f"max must be numeric: {twc.get('max')}"

        # platform: list with at least 1 entry
        assert "platform" in body, f"Missing platform in {json.dumps(body)}"
        platform = body["platform"]
        assert isinstance(platform, list), f"platform must be list, got {type(platform)}"
        assert len(platform) >= 1, f"platform must have at least 1 entry: {platform}"
        for entry in platform:
            assert "name" in entry, f"platform entry missing name: {entry}"
            assert "resolution" in entry, f"platform entry missing resolution: {entry}"
            assert "bitrate" in entry, f"platform entry missing bitrate: {entry}"
            assert "format" in entry, f"platform entry missing format: {entry}"
            assert "aspect_ratio" in entry, f"platform entry missing aspect_ratio: {entry}"

        # category
        assert "category" in body, f"Missing category in {json.dumps(body)}"
        category = body["category"]
        assert isinstance(category, dict), f"category must be dict, got {type(category)}"
        assert "level1" in category, f"category missing level1: {category}"
        assert "level2" in category, f"category missing level2: {category}"

        # version
        assert "version" in body, f"Missing version in {json.dumps(body)}"
        assert body["version"] >= 1, f"version must be >= 1, got {body['version']}"

    def test_get_artifact_invalid_phase_returns_404(self):
        """GET /projects/{id}/phases/99/artifact returns 404 INVALID_PHASE."""
        with httpx.Client(timeout=httpx.Timeout(30.0)) as client:
            # Create a project to have a valid project_id
            created = _create_project(
                client,
                "Invalid Phase Test",
                "A description long enough for invalid phase contract validation",
            )
            project_id = created.get("project_id") or created.get("id")
            assert project_id

            resp = client.get(f"{BASE_URL}/projects/{project_id}/phases/99/artifact")

        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"

        body = resp.json()
        assert "error" in body, f"Expected error envelope, got {json.dumps(body)}"
        error = body["error"]
        assert (
            error.get("code") == "INVALID_PHASE"
        ), f"Expected INVALID_PHASE, got {error.get('code')}"


# ---- T010: POST /api/projects/{id}/chat ----------------------------------


class TestChatContract:
    """Contract tests for POST /api/projects/{project_id}/chat (rest-api.md section 4)."""

    VALID_ACTIONS = {
        "revise",
        "regenerate",
        "clarify",
        "refine_requirements",
        "regenerate_section",
    }

    def test_chat_returns_200_with_intent_response(self):
        """POST /projects/{id}/chat with valid message returns 200 and intent shape."""
        with httpx.Client(timeout=httpx.Timeout(60.0)) as client:
            # Create a project first
            created = _create_project(
                client,
                "Chat Contract Test",
                "A description long enough for chat endpoint contract validation",
            )
            project_id = created.get("project_id") or created.get("id")
            assert project_id, f"Cannot extract project_id from: {json.dumps(created)}"

            resp = client.post(
                f"{BASE_URL}/projects/{project_id}/chat",
                json={"message": "改成8-12分钟", "context": {}},
            )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

        body = resp.json()

        # Required top-level fields
        assert "project_id" in body, f"Missing project_id in {json.dumps(body)}"
        assert body["project_id"] == project_id

        assert "action" in body, f"Missing action in {json.dumps(body)}"
        assert (
            body["action"] in self.VALID_ACTIONS
        ), f"action must be one of {self.VALID_ACTIONS}, got '{body['action']}'"

        assert "response" in body, f"Missing response in {json.dumps(body)}"
        assert isinstance(
            body["response"], str
        ), f"response must be a string, got {type(body['response'])}"
        assert len(body["response"]) > 0, "response must be non-empty"

        assert body.get("phase") == 0, f"phase must be 0, got {body.get('phase')}"

        assert "clarify_count" in body, f"Missing clarify_count in {json.dumps(body)}"
        assert isinstance(
            body["clarify_count"], int
        ), f"clarify_count must be int, got {type(body['clarify_count'])}"

        assert "task_ledger" in body, f"Missing task_ledger in {json.dumps(body)}"
        assert isinstance(
            body["task_ledger"], list
        ), f"task_ledger must be a list, got {type(body['task_ledger'])}"

    def test_chat_empty_message_returns_error(self):
        """POST /projects/{id}/chat with empty message returns 4xx."""
        with httpx.Client(timeout=httpx.Timeout(30.0)) as client:
            created = _create_project(
                client,
                "Chat Empty Message Test",
                "A description long enough for empty message contract validation",
            )
            project_id = created.get("project_id") or created.get("id")
            assert project_id

            resp = client.post(
                f"{BASE_URL}/projects/{project_id}/chat",
                json={"message": "", "context": {}},
            )

        assert resp.status_code in (
            400,
            422,
        ), f"Expected 400 or 422, got {resp.status_code}: {resp.text}"

    def test_chat_nonexistent_project_returns_404(self):
        """POST /projects/{nonexistent_id}/chat returns 404 NOT_FOUND."""
        with httpx.Client(timeout=httpx.Timeout(30.0)) as client:
            resp = client.post(
                f"{BASE_URL}/projects/nonexistent_proj_id/chat",
                json={"message": "test", "context": {}},
            )

        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"


# ---- T024: POST /api/projects/{id}/advance --------------------------------


VALID_ADVANCE_STATUSES = {"advanced", "already_advanced", "gate_failed", "gate_in_progress"}


class TestAdvanceContract:
    """Contract tests for POST /api/projects/{project_id}/advance (rest-api.md section 5)."""

    def test_advance_returns_200_with_status_field(self):
        """POST /projects/{id}/advance returns response with status and current_phase.

        Waits for the phase 0 artifact to be generated before attempting advance,
        since the advance gate checks that the current phase has a completed artifact.
        """
        with httpx.Client(timeout=httpx.Timeout(90.0)) as client:
            # Create a project
            created = _create_project(
                client,
                "Advance Contract Test",
                "A description long enough for advance endpoint contract validation",
            )
            project_id = created.get("project_id") or created.get("id")
            assert project_id, f"Cannot extract project_id from: {json.dumps(created)}"

            # Wait for phase 0 artifact to be generated (gate requires it)
            artifact_url = f"{BASE_URL}/projects/{project_id}/phases/0/artifact"
            deadline = time.time() + 60.0
            artifact_ready = False

            while time.time() < deadline:
                resp = client.get(artifact_url)
                if resp.status_code == 200:
                    body = resp.json()
                    if body.get("artifact_data") is not None:
                        artifact_ready = True
                        break
                elif resp.status_code != 404:
                    break
                time.sleep(2.0)

            if not artifact_ready:
                pytest.fail(f"Phase 0 artifact not ready within 60s for project {project_id}")

            # Advance to next phase
            resp = client.post(f"{BASE_URL}/projects/{project_id}/advance")

        # Status code depends on gate outcome, but must be one of the known codes
        assert resp.status_code in (
            200,
            409,
            422,
        ), f"Expected 200/409/422, got {resp.status_code}: {resp.text}"

        body = resp.json()

        # Required fields: status and current_phase
        assert "status" in body, f"Missing status in {json.dumps(body)}"
        assert (
            body["status"] in VALID_ADVANCE_STATUSES
        ), f"status must be one of {VALID_ADVANCE_STATUSES}, got '{body['status']}'"

        assert "current_phase" in body, f"Missing current_phase in {json.dumps(body)}"
        assert isinstance(
            body["current_phase"], int
        ), f"current_phase must be int, got {type(body['current_phase'])}"

        # When advanced, from_phase is set and error_code is None
        if body["status"] == "advanced":
            assert (
                "from_phase" in body
            ), f"Missing from_phase in advanced response: {json.dumps(body)}"
            assert (
                body.get("error_code") is None
            ), f"error_code should be None when advanced, got '{body.get('error_code')}'"

        # When gate_failed or gate_in_progress, error_code is set
        if body["status"] in ("gate_failed", "gate_in_progress"):
            assert (
                "error_code" in body
            ), f"Missing error_code in {body['status']} response: {json.dumps(body)}"
            assert (
                body["error_code"] is not None
            ), f"error_code must not be None for {body['status']}"

    def test_advance_nonexistent_project_returns_404(self):
        """POST /projects/{nonexistent_id}/advance returns 404 NOT_FOUND."""
        with httpx.Client(timeout=httpx.Timeout(30.0)) as client:
            resp = client.post(
                f"{BASE_URL}/projects/nonexistent_proj_id/advance",
            )

        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"

        body = resp.json()
        # Backend returns HTTPException detail directly: {"detail": "Project not found"}
        # or structured error envelope. Accept either.
        if "detail" in body:
            assert "not found" in body["detail"].lower(), f"Expected 'not found' in detail: {body}"
        else:
            assert "error" in body, f"Expected error envelope, got {json.dumps(body)}"

    def test_advance_before_artifact_returns_gate_blocked(self):
        """POST /projects/{id}/advance immediately after creation returns gate blocked.

        The advance gate for phase 0 requires the artifact to exist, so advancing
        before the async artifact generation completes should be rejected with
        either gate_in_progress (409) or gate_failed (422).
        """
        with httpx.Client(timeout=httpx.Timeout(30.0)) as client:
            created = _create_project(
                client,
                "Advance Blocked Test",
                "A description long enough for advance gate block contract validation",
            )
            project_id = created.get("project_id") or created.get("id")
            assert project_id, f"Cannot extract project_id from: {json.dumps(created)}"

            # Advance immediately (artifact not yet generated)
            resp = client.post(f"{BASE_URL}/projects/{project_id}/advance")

        # Gate should block — status code is either 409 or 422
        assert resp.status_code in (
            409,
            422,
        ), f"Expected 409 or 422 (gate blocked), got {resp.status_code}: {resp.text}"

        body = resp.json()
        assert "status" in body, f"Missing status in {json.dumps(body)}"
        assert body["status"] in (
            "gate_in_progress",
            "gate_failed",
        ), f"Expected gate_in_progress or gate_failed, got '{body['status']}'"

        assert (
            "error_code" in body
        ), f"Missing error_code in gate block response: {json.dumps(body)}"
        assert body["error_code"] is not None, f"error_code must not be None for {body['status']}"

        assert "current_phase" in body, f"Missing current_phase in {json.dumps(body)}"
        assert isinstance(
            body["current_phase"], int
        ), f"current_phase must be int, got {type(body['current_phase'])}"


# ---- T032: WebSocket events contract -------------------------------------

try:
    import websockets

    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False


VALID_WS_EVENT_TYPES = {
    "task.created",
    "task.started",
    "task.completed",
    "artifact.updated",
    "review.completed",
    "phase.advanced",
    "error",
}


class TestWebSocketEventsContract:
    """Contract tests for WebSocket events at ws://localhost:8000/ws/{project_id}.

    Validates that the server emits JSON event messages over the WebSocket
    connection when project state changes occur.
    """

    @pytest.mark.skipif(
        not WEBSOCKETS_AVAILABLE,
        reason="websockets library not installed (pip install websockets)",
    )
    def test_websocket_events_received_on_project_create(self):
        """Connect via WebSocket, trigger a chat message, and verify events arrive.

        1. Create a project via REST to get a project_id.
        2. Connect to ws://localhost:8000/ws/{project_id}.
        3. Send a chat message via REST (triggers backend events).
        4. Listen for WebSocket messages for up to 15 seconds.
        5. Assert at least one event message is received (JSON with a `type` field).
        """
        events_received = []

        async def _run():
            import asyncio

            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as rest_client:
                # Step 1: Create a project via REST
                resp = await rest_client.post(
                    f"{BASE_URL}/projects",
                    json={
                        "title": "WebSocket Contract Test",
                        "description": (
                            "A description long enough for WebSocket event "
                            "contract validation tests"
                        ),
                    },
                )
                assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
                created = resp.json()
                project_id = created.get("project_id") or created.get("id")
                assert project_id, f"Cannot extract project_id from: {json.dumps(created)}"

                # Step 2: Connect via WebSocket
                ws_url = f"ws://localhost:8000/ws/{project_id}"
                try:
                    async with websockets.connect(ws_url) as ws:
                        # Step 3: Send a chat message via REST (triggers backend events)
                        await rest_client.post(
                            f"{BASE_URL}/projects/{project_id}/chat",
                            json={
                                "message": "trigger WebSocket events test message",
                                "context": {},
                            },
                        )

                        # Step 4: Listen for WebSocket messages (up to 15 seconds)
                        try:
                            while True:
                                raw = await asyncio.wait_for(ws.recv(), timeout=15.0)
                                try:
                                    event = json.loads(raw)
                                except json.JSONDecodeError:
                                    # Non-JSON message — skip
                                    continue
                                if isinstance(event, dict) and "type" in event:
                                    events_received.append(event)
                                    # Stop once we have enough evidence
                                    if len(events_received) >= 1:
                                        break
                        except TimeoutError:
                            # No more messages within timeout — ok
                            pass
                except Exception as exc:
                    pytest.fail(f"WebSocket connection to {ws_url} failed: {exc}")

        import asyncio

        asyncio.run(_run())

        # Step 5: Assert at least one event message was received
        assert len(events_received) >= 1, (
            "Expected at least 1 WebSocket event message, "
            "but none were received within 15 seconds. "
            "Check that the backend WebSocket endpoint is running and "
            "emitting events on project state changes."
        )

        # Verify the event has the expected shape
        first_event = events_received[0]
        assert "type" in first_event, f"Event must have a 'type' field: {json.dumps(first_event)}"
        assert first_event["type"] in VALID_WS_EVENT_TYPES, (
            f"Event type '{first_event['type']}' not in known event types "
            f"{VALID_WS_EVENT_TYPES}"
        )
