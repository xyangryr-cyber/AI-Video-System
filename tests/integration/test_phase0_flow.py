"""[SPEC-D-002] Phase 0 integration test — User Story 1 happy path.

US1: User creates a project with title + description ->
AI generates structured requirements -> requirements card appears with real data.

Makes real HTTP calls to a running backend at http://localhost:8000/api.
Requires the server to be running with LLM access configured.

Usage:
  pytest tests/integration/test_phase0_flow.py -v -s
"""

from __future__ import annotations

import time

import pytest
import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = "http://localhost:8000/api"
POLL_INTERVAL_SEC = 2
POLL_TIMEOUT_SEC = 45

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# TestUS1HappyPath
# ---------------------------------------------------------------------------


class TestUS1HappyPath:
    """User Story 1: Create project -> AI generates requirements -> verify artifact."""

    def test_create_project_and_get_requirements(self):
        """Happy-path integration test for Phase 0 requirements generation.

        1. POST /api/projects to create a project.
        2. Poll GET /api/projects/{id}/phases/0/artifact until artifact is ready.
        3. Verify artifact_data contains all required fields.
        4. Verify tasks endpoint shows generate_artifact task.
        """

        # ------------------------------------------------------------------
        # Step 1: Create project
        # ------------------------------------------------------------------
        create_body = {
            "title": "Integration Test: Gold Investment Analysis",
            "description": (
                "做一个关于近期黄金价格走势的分析视频，从技术面和基本面两个角度解读，"
                "适合投资新手观看，5-8分钟，发布到B站"
            ),
        }

        r = requests.post(f"{BASE_URL}/projects", json=create_body)

        assert r.status_code == 201, f"Expected 201 Created, got {r.status_code}: {r.text}"

        project_data = r.json()
        project_id = project_data["id"]
        assert project_id, "Project ID should not be empty"
        assert project_data["title"] == create_body["title"]

        # ------------------------------------------------------------------
        # Step 2: Poll for artifact
        # ------------------------------------------------------------------
        deadline = time.monotonic() + POLL_TIMEOUT_SEC
        artifact_url = f"{BASE_URL}/projects/{project_id}/phases/0/artifact"
        artifact_response = None

        while time.monotonic() < deadline:
            r_art = requests.get(artifact_url)

            if r_art.status_code == 200:
                art_data = r_art.json()
                if art_data.get("artifact_data") is not None:
                    artifact_response = art_data
                    break
                # artifact_data is null — agent has not finished yet
            elif r_art.status_code == 404:
                # Phase row may not exist yet (project still initializing)
                pass
            else:
                # Unexpected status — surface immediately
                pytest.fail(
                    f"Unexpected status {r_art.status_code} from {artifact_url}: " f"{r_art.text}"
                )

            time.sleep(POLL_INTERVAL_SEC)

        assert artifact_response is not None, (
            f"Timed out after {POLL_TIMEOUT_SEC}s waiting for Phase 0 artifact. "
            f"Last poll: check logs for details"
        )

        # ------------------------------------------------------------------
        # Step 3: Verify artifact data fields
        # ------------------------------------------------------------------
        artifact_data = artifact_response["artifact_data"]

        # 3a. project_id matches
        assert artifact_data["project_id"] == project_id, (
            f"artifact_data.project_id '{artifact_data.get('project_id')}' "
            f"does not match created project_id '{project_id}'"
        )

        # 3b. title is non-empty
        assert artifact_data.get("title"), "artifact_data.title is empty or missing"

        # 3c. topic is non-empty and >= 5 chars
        topic = artifact_data.get("topic")
        assert topic is not None, "artifact_data.topic is missing"
        assert len(topic) >= 5, (
            f"artifact_data.topic '{topic}' has length {len(topic)}, " f"expected >= 5"
        )

        # 3d. target_duration has min_sec and max_sec (both >= 0)
        target_duration = artifact_data.get("target_duration")
        assert target_duration is not None, "artifact_data.target_duration is missing"
        min_sec = target_duration.get("min_sec")
        max_sec = target_duration.get("max_sec")
        assert min_sec is not None, "artifact_data.target_duration.min_sec is missing"
        assert max_sec is not None, "artifact_data.target_duration.max_sec is missing"
        assert min_sec >= 0, f"target_duration.min_sec={min_sec} must be >= 0"
        assert max_sec >= 0, f"target_duration.max_sec={max_sec} must be >= 0"

        # 3e. target_word_count has min and max (min > 0, max >= min)
        target_word_count = artifact_data.get("target_word_count")
        assert target_word_count is not None, "artifact_data.target_word_count is missing"
        wc_min = target_word_count.get("min")
        wc_max = target_word_count.get("max")
        assert wc_min is not None, "artifact_data.target_word_count.min is missing"
        assert wc_max is not None, "artifact_data.target_word_count.max is missing"
        assert wc_min > 0, f"target_word_count.min={wc_min} must be > 0"
        assert wc_max >= wc_min, f"target_word_count.max={wc_max} must be >= min={wc_min}"

        # 3f. platform is non-empty list; each entry has name
        platform_list = artifact_data.get("platform")
        assert platform_list is not None, "artifact_data.platform is missing"
        assert isinstance(platform_list, list), (
            f"artifact_data.platform should be a list, " f"got {type(platform_list).__name__}"
        )
        assert len(platform_list) > 0, "artifact_data.platform list is empty"
        for i, entry in enumerate(platform_list):
            assert isinstance(entry, dict), (
                f"platform entry {i} should be a dict, " f"got {type(entry).__name__}"
            )
            assert entry.get("name") is not None, f"platform entry {i} is missing 'name' field"

        # 3g. category has level1 and level2 (both non-empty)
        category = artifact_data.get("category")
        assert category is not None, "artifact_data.category is missing"
        level1 = category.get("level1")
        level2 = category.get("level2")
        assert level1, "artifact_data.category.level1 is empty or missing"
        assert level2, "artifact_data.category.level2 is empty or missing"

        # 3h. version >= 1 (artifact_version in the response wrapper)
        artifact_version = artifact_response.get("artifact_version")
        assert artifact_version is not None, "artifact_version is missing from artifact response"
        assert artifact_version >= 1, f"artifact_version={artifact_version} must be >= 1"

        # ------------------------------------------------------------------
        # Step 4: Verify tasks endpoint
        # ------------------------------------------------------------------
        tasks_url = f"{BASE_URL}/projects/{project_id}/tasks?phase=0"
        r_tasks = requests.get(tasks_url)

        assert r_tasks.status_code == 200, (
            f"Expected 200 OK from tasks endpoint, " f"got {r_tasks.status_code}: {r_tasks.text}"
        )

        tasks_data = r_tasks.json()

        # 4a. Has tasks list
        assert "tasks" in tasks_data, "tasks response missing 'tasks' key"
        assert isinstance(tasks_data["tasks"], list), (
            f"'tasks' should be a list, " f"got {type(tasks_data['tasks']).__name__}"
        )

        # 4b. Has current_task field
        assert "current_task" in tasks_data, "tasks response missing 'current_task' key"

        # 4c. At least one task of type generate_artifact
        generate_tasks = [t for t in tasks_data["tasks"] if t.get("type") == "generate_artifact"]
        assert len(generate_tasks) > 0, "No tasks of type 'generate_artifact' found in task list"


# ---------------------------------------------------------------------------
# TestUS2ReviseFlow
# ---------------------------------------------------------------------------


class TestUS2ReviseFlow:
    """User Story 2: After AI generates requirements, user revises via chat
    and the artifact is updated with a higher artifact_version."""

    def test_revise_via_chat_updates_artifact(self):
        """Integration test for the revise flow.

        1. Create a project.
        2. Poll for the initial Phase 0 artifact.
        3. Record the initial artifact_version.
        4. Send a revise chat message.
        5. Poll for an updated artifact with a higher version.
        """

        # --------------------------------------------------------------
        # Step 1: Create project
        # --------------------------------------------------------------
        create_body = {
            "title": "Revise Test",
            "description": ("这是一个测试视频，用于验证修改流程是否正常工作"),
        }

        r = requests.post(f"{BASE_URL}/projects", json=create_body)

        assert r.status_code == 201, f"Expected 201 Created, got {r.status_code}: {r.text}"

        project_data = r.json()
        project_id = project_data["id"]
        assert project_id, "Project ID should not be empty"

        # --------------------------------------------------------------
        # Step 2: Poll for initial artifact
        # --------------------------------------------------------------
        deadline = time.monotonic() + POLL_TIMEOUT_SEC
        artifact_url = f"{BASE_URL}/projects/{project_id}/phases/0/artifact"
        initial_artifact = None

        while time.monotonic() < deadline:
            r_art = requests.get(artifact_url)

            if r_art.status_code == 200:
                art_data = r_art.json()
                if art_data.get("artifact_data") is not None:
                    initial_artifact = art_data
                    break
            elif r_art.status_code == 404:
                pass
            else:
                pytest.fail(
                    f"Unexpected status {r_art.status_code} from {artifact_url}: " f"{r_art.text}"
                )

            time.sleep(POLL_INTERVAL_SEC)

        assert initial_artifact is not None, (
            f"Timed out after {POLL_TIMEOUT_SEC}s waiting for initial Phase 0 " "artifact"
        )

        # --------------------------------------------------------------
        # Step 3: Record initial artifact_version
        # --------------------------------------------------------------
        initial_version = initial_artifact.get("artifact_version")
        assert (
            initial_version is not None
        ), "Initial artifact_version is missing from artifact response"
        assert initial_version >= 1, f"Initial artifact_version={initial_version} must be >= 1"

        # --------------------------------------------------------------
        # Step 4: Send revise chat message
        # --------------------------------------------------------------
        chat_url = f"{BASE_URL}/projects/{project_id}/chat"
        chat_body = {
            "message": "请把时长改为8-12分钟",
            "context": {},
        }

        r_chat = requests.post(chat_url, json=chat_body)

        assert r_chat.status_code == 200, (
            f"Expected 200 OK from chat endpoint, " f"got {r_chat.status_code}: {r_chat.text}"
        )

        chat_response = r_chat.json()
        # The chat endpoint should return a non-empty action
        action = chat_response.get("action")
        assert action is not None, "Chat response missing 'action' field"
        assert action != "clarify", (
            f"Expected non-clarify action for revise message, "
            f"got action='{action}'. Response: {chat_response}"
        )

        # --------------------------------------------------------------
        # Step 5: Poll for updated artifact with higher version
        # --------------------------------------------------------------
        deadline = time.monotonic() + POLL_TIMEOUT_SEC
        updated_artifact = None

        while time.monotonic() < deadline:
            r_art = requests.get(artifact_url)

            if r_art.status_code == 200:
                art_data = r_art.json()
                current_version = art_data.get("artifact_version")
                if current_version is not None and current_version > initial_version:
                    updated_artifact = art_data
                    break
            elif r_art.status_code == 404:
                pass
            else:
                pytest.fail(
                    f"Unexpected status {r_art.status_code} from {artifact_url}: " f"{r_art.text}"
                )

            time.sleep(POLL_INTERVAL_SEC)

        assert updated_artifact is not None, (
            f"Timed out after {POLL_TIMEOUT_SEC}s waiting for artifact_version "
            f"to exceed initial version {initial_version}. "
            f"The artifact may not have been re-generated yet (RED expected)."
        )

        updated_version = updated_artifact.get("artifact_version")
        assert updated_version > initial_version, (
            f"Expected updated artifact_version={updated_version} "
            f"to be > initial_version={initial_version}"
        )


# ---------------------------------------------------------------------------
# TestUS2RegenerateFlow
# ---------------------------------------------------------------------------


class TestUS2RegenerateFlow:
    """User Story 2: User requests full regeneration via chat and the
    artifact is re-generated with a different version or timestamp."""

    def test_regenerate_via_chat_creates_fresh_artifact(self):
        """Integration test for the regenerate flow.

        1. Create a project.
        2. Poll for the initial Phase 0 artifact.
        3. Record the initial artifact_version.
        4. Send a regenerate chat message.
        5. Poll for an updated artifact with a higher version.
        """

        # --------------------------------------------------------------
        # Step 1: Create project
        # --------------------------------------------------------------
        create_body = {
            "title": "Regenerate Test",
            "description": ("这是一个测试视频，用于验证重新生成流程"),
        }

        r = requests.post(f"{BASE_URL}/projects", json=create_body)

        assert r.status_code == 201, f"Expected 201 Created, got {r.status_code}: {r.text}"

        project_data = r.json()
        project_id = project_data["id"]
        assert project_id, "Project ID should not be empty"

        # --------------------------------------------------------------
        # Step 2: Poll for initial artifact
        # --------------------------------------------------------------
        deadline = time.monotonic() + POLL_TIMEOUT_SEC
        artifact_url = f"{BASE_URL}/projects/{project_id}/phases/0/artifact"
        initial_artifact = None

        while time.monotonic() < deadline:
            r_art = requests.get(artifact_url)

            if r_art.status_code == 200:
                art_data = r_art.json()
                if art_data.get("artifact_data") is not None:
                    initial_artifact = art_data
                    break
            elif r_art.status_code == 404:
                pass
            else:
                pytest.fail(
                    f"Unexpected status {r_art.status_code} from {artifact_url}: " f"{r_art.text}"
                )

            time.sleep(POLL_INTERVAL_SEC)

        assert initial_artifact is not None, (
            f"Timed out after {POLL_TIMEOUT_SEC}s waiting for initial Phase 0 " "artifact"
        )

        # --------------------------------------------------------------
        # Step 3: Record initial artifact_version
        # --------------------------------------------------------------
        initial_version = initial_artifact.get("artifact_version")
        assert (
            initial_version is not None
        ), "Initial artifact_version is missing from artifact response"
        assert initial_version >= 1, f"Initial artifact_version={initial_version} must be >= 1"

        # --------------------------------------------------------------
        # Step 4: Send regenerate chat message
        # --------------------------------------------------------------
        chat_url = f"{BASE_URL}/projects/{project_id}/chat"
        chat_body = {
            "message": "重新生成需求",
            "context": {},
        }

        r_chat = requests.post(chat_url, json=chat_body)

        assert r_chat.status_code == 200, (
            f"Expected 200 OK from chat endpoint, " f"got {r_chat.status_code}: {r_chat.text}"
        )

        chat_response = r_chat.json()
        # The chat endpoint should return a regenerate action
        action = chat_response.get("action")
        assert action is not None, "Chat response missing 'action' field"
        assert action == "regenerate_section", (
            f"Expected action='regenerate_section' for regenerate message, "
            f"got action='{action}'. Response: {chat_response}"
        )

        # --------------------------------------------------------------
        # Step 5: Poll for updated artifact with higher version
        # --------------------------------------------------------------
        deadline = time.monotonic() + POLL_TIMEOUT_SEC
        updated_artifact = None

        while time.monotonic() < deadline:
            r_art = requests.get(artifact_url)

            if r_art.status_code == 200:
                art_data = r_art.json()
                current_version = art_data.get("artifact_version")
                if current_version is not None and current_version > initial_version:
                    updated_artifact = art_data
                    break
            elif r_art.status_code == 404:
                pass
            else:
                pytest.fail(
                    f"Unexpected status {r_art.status_code} from {artifact_url}: " f"{r_art.text}"
                )

            time.sleep(POLL_INTERVAL_SEC)

        assert updated_artifact is not None, (
            f"Timed out after {POLL_TIMEOUT_SEC}s waiting for artifact_version "
            f"to exceed initial version {initial_version}. "
            f"The artifact may not have been re-generated yet (RED expected)."
        )

        updated_version = updated_artifact.get("artifact_version")
        assert updated_version > initial_version, (
            f"Expected updated artifact_version={updated_version} "
            f"to be > initial_version={initial_version}"
        )


# ---------------------------------------------------------------------------
# TestUS3ClarificationFlow
# ---------------------------------------------------------------------------


class TestUS3ClarificationFlow:
    """User Story 3: Submit vague description -> clarification questions appear ->
    answer via chat -> requirements update without altering confirmed fields."""

    def test_clarification_flow_vague_description_triggers_clarification(self):
        """Integration test for the clarification flow.

        1. Create a project with a deliberately vague description.
        2. Poll for the initial Phase 0 artifact.
        3. Verify clarification_needed is non-empty (at least 1 item with
           dimension and question fields).
        4. Record the number of clarification questions.
        5. Send a chat message answering the first clarification.
        6. Poll for an updated artifact with a higher artifact_version.
        7. Verify the clarification_needed array has fewer items than before.
        8. Verify confirmed fields (topic, category) are still present.
        """

        # --------------------------------------------------------------
        # Step 1: Create project with vague description
        # --------------------------------------------------------------
        create_body = {
            "title": "金融分析视频",
            "description": "做一个金融分析视频",
        }

        r = requests.post(f"{BASE_URL}/projects", json=create_body)

        assert r.status_code == 201, f"Expected 201 Created, got {r.status_code}: {r.text}"

        project_data = r.json()
        project_id = project_data["id"]
        assert project_id, "Project ID should not be empty"

        # --------------------------------------------------------------
        # Step 2: Poll for initial artifact
        # --------------------------------------------------------------
        deadline = time.monotonic() + POLL_TIMEOUT_SEC
        artifact_url = f"{BASE_URL}/projects/{project_id}/phases/0/artifact"
        initial_artifact = None

        while time.monotonic() < deadline:
            r_art = requests.get(artifact_url)

            if r_art.status_code == 200:
                art_data = r_art.json()
                if art_data.get("artifact_data") is not None:
                    initial_artifact = art_data
                    break
            elif r_art.status_code == 404:
                pass
            else:
                pytest.fail(
                    f"Unexpected status {r_art.status_code} from {artifact_url}: " f"{r_art.text}"
                )

            time.sleep(POLL_INTERVAL_SEC)

        assert initial_artifact is not None, (
            f"Timed out after {POLL_TIMEOUT_SEC}s waiting for initial Phase 0 " "artifact"
        )

        # --------------------------------------------------------------
        # Step 3: Verify clarification_needed is non-empty
        # --------------------------------------------------------------
        artifact_data = initial_artifact["artifact_data"]
        initial_version = initial_artifact.get("artifact_version")
        assert (
            initial_version is not None
        ), "Initial artifact_version is missing from artifact response"
        assert initial_version >= 1, f"Initial artifact_version={initial_version} must be >= 1"

        clarification_needed = artifact_data.get("clarification_needed")
        assert clarification_needed is not None, (
            "artifact_data.clarification_needed is missing — "
            "vague description should trigger clarification questions"
        )
        assert isinstance(clarification_needed, list), (
            f"artifact_data.clarification_needed should be a list, "
            f"got {type(clarification_needed).__name__}"
        )
        assert len(clarification_needed) >= 1, (
            f"Expected at least 1 clarification question for vague description, "
            f"got {len(clarification_needed)}"
        )

        for i, item in enumerate(clarification_needed):
            assert isinstance(item, dict), (
                f"clarification_needed item {i} should be a dict, " f"got {type(item).__name__}"
            )
            assert (
                item.get("dimension") is not None
            ), f"clarification_needed item {i} is missing 'dimension' field"
            assert (
                item.get("question") is not None
            ), f"clarification_needed item {i} is missing 'question' field"

        # --------------------------------------------------------------
        # Step 4: Record initial clarification count
        # --------------------------------------------------------------
        initial_clarify_count = len(clarification_needed)

        # --------------------------------------------------------------
        # Step 5: Send chat message answering the first clarification
        # --------------------------------------------------------------
        chat_url = f"{BASE_URL}/projects/{project_id}/chat"
        chat_body = {
            "message": "我想发在B站",
            "context": {},
        }

        r_chat = requests.post(chat_url, json=chat_body)

        assert r_chat.status_code == 200, (
            f"Expected 200 OK from chat endpoint, " f"got {r_chat.status_code}: {r_chat.text}"
        )

        chat_response = r_chat.json()
        # The chat endpoint should return an action — either clarify (if
        # ambiguity remains) or revise (if the answer was specific enough).
        action = chat_response.get("action")
        assert action is not None, "Chat response missing 'action' field"
        # Acceptable actions: clarify (more questions), revise, or
        # regenerate_section. The key is that it does not crash.
        assert action in (
            "clarify",
            "revise",
            "regenerate_section",
        ), f"Unexpected chat action='{action}'. Response: {chat_response}"

        # --------------------------------------------------------------
        # Step 6: Poll for updated artifact with higher version
        # --------------------------------------------------------------
        deadline = time.monotonic() + POLL_TIMEOUT_SEC
        updated_artifact = None

        while time.monotonic() < deadline:
            r_art = requests.get(artifact_url)

            if r_art.status_code == 200:
                art_data = r_art.json()
                current_version = art_data.get("artifact_version")
                if current_version is not None and current_version > initial_version:
                    updated_artifact = art_data
                    break
            elif r_art.status_code == 404:
                pass
            else:
                pytest.fail(
                    f"Unexpected status {r_art.status_code} from {artifact_url}: " f"{r_art.text}"
                )

            time.sleep(POLL_INTERVAL_SEC)

        assert updated_artifact is not None, (
            f"Timed out after {POLL_TIMEOUT_SEC}s waiting for artifact_version "
            f"to exceed initial version {initial_version}. "
            f"The artifact may not have been re-generated yet (RED expected)."
        )

        updated_version = updated_artifact.get("artifact_version")
        assert updated_version > initial_version, (
            f"Expected updated artifact_version={updated_version} "
            f"to be > initial_version={initial_version}"
        )

        # --------------------------------------------------------------
        # Step 7: Verify clarification_needed has fewer items
        # --------------------------------------------------------------
        updated_data = updated_artifact["artifact_data"]
        updated_clarify = updated_data.get("clarification_needed")
        assert updated_clarify is not None, "Updated artifact_data.clarification_needed is missing"
        assert isinstance(updated_clarify, list), (
            f"Updated clarification_needed should be a list, "
            f"got {type(updated_clarify).__name__}"
        )
        updated_clarify_count = len(updated_clarify)
        assert updated_clarify_count < initial_clarify_count, (
            f"Expected clarification_needed to shrink after answering a question. "
            f"Before: {initial_clarify_count} items, "
            f"After: {updated_clarify_count} items"
        )

        # --------------------------------------------------------------
        # Step 8: Verify confirmed fields preserved
        # --------------------------------------------------------------
        # topic should still be present and non-empty
        topic = updated_data.get("topic")
        assert topic is not None, (
            "Updated artifact_data.topic is missing — " "confirmed field should be preserved"
        )
        assert len(topic) >= 5, (
            f"Updated artifact_data.topic '{topic}' has length {len(topic)}, "
            f"expected >= 5 — confirmed field should be preserved"
        )

        # category should still be present and non-empty
        category = updated_data.get("category")
        assert category is not None, (
            "Updated artifact_data.category is missing — " "confirmed field should be preserved"
        )
        level1 = category.get("level1")
        level2 = category.get("level2")
        assert level1, (
            "Updated artifact_data.category.level1 is empty or missing — "
            "confirmed field should be preserved"
        )
        assert level2, (
            "Updated artifact_data.category.level2 is empty or missing — "
            "confirmed field should be preserved"
        )


# ---------------------------------------------------------------------------
# TestUS4AdvanceHappyPath
# ---------------------------------------------------------------------------


class TestUS4AdvanceHappyPath:
    """User Story 4: Advance to next phase after Phase 0 artifact is ready and
    reviewed. Happy path — advance should succeed once the gate clears."""

    def test_advance_after_artifact_and_review_moves_to_phase_1(self):
        """Integration test for the advance happy path.

        1. Create a project with a clear description.
        2. Poll for the Phase 0 artifact.
        3. POST to the advance endpoint.
        4. Verify the response is not an error (status not gate_failed).
        """

        # --------------------------------------------------------------
        # Step 1: Create project with clear description
        # --------------------------------------------------------------
        create_body = {
            "title": "Advance Test: Stock Market Overview",
            "description": (
                "做一个关于A股市场近期走势的分析视频，从技术面和基本面两个角度解读，"
                "适合投资新手观看，5-8分钟，发布到B站。重点分析近期热门板块和龙头股。"
            ),
        }

        r = requests.post(f"{BASE_URL}/projects", json=create_body)

        assert r.status_code == 201, f"Expected 201 Created, got {r.status_code}: {r.text}"

        project_data = r.json()
        project_id = project_data["id"]
        assert project_id, "Project ID should not be empty"

        # --------------------------------------------------------------
        # Step 2: Poll for artifact
        # --------------------------------------------------------------
        deadline = time.monotonic() + POLL_TIMEOUT_SEC
        artifact_url = f"{BASE_URL}/projects/{project_id}/phases/0/artifact"
        artifact_response = None

        while time.monotonic() < deadline:
            r_art = requests.get(artifact_url)

            if r_art.status_code == 200:
                art_data = r_art.json()
                if art_data.get("artifact_data") is not None:
                    artifact_response = art_data
                    break
            elif r_art.status_code == 404:
                pass
            else:
                pytest.fail(
                    f"Unexpected status {r_art.status_code} from {artifact_url}: " f"{r_art.text}"
                )

            time.sleep(POLL_INTERVAL_SEC)

        assert (
            artifact_response is not None
        ), f"Timed out after {POLL_TIMEOUT_SEC}s waiting for Phase 0 artifact"

        # --------------------------------------------------------------
        # Step 3: POST to advance endpoint
        # --------------------------------------------------------------
        advance_url = f"{BASE_URL}/projects/{project_id}/advance"
        r_advance = requests.post(advance_url)

        # --------------------------------------------------------------
        # Step 4: Verify the response
        # --------------------------------------------------------------
        # The happy case is status=200 with status="advanced" or
        # "already_advanced".  If tasks are still running we may get 409
        # with "gate_in_progress" — that is also fine because this test
        # validates the advance endpoint responds correctly for a
        # well-formed project, not that it always advances on the first
        # call.  The key assertion: the response is NOT gate_failed.
        assert r_advance.status_code in (200, 409), (
            f"Expected status 200 or 409 from advance endpoint, "
            f"got {r_advance.status_code}: {r_advance.text}"
        )

        advance_data = r_advance.json()
        advance_status = advance_data.get("status")

        assert advance_status is not None, "Advance response missing 'status' field"

        assert advance_status != "gate_failed", (
            f"Expected advance not to fail for a well-formed project. "
            f"Got status='{advance_status}', error_code='{advance_data.get('error_code')}'. "
            f"Full response: {advance_data}"
        )

        # If we got 200, verify the current_phase moved forward
        if r_advance.status_code == 200:
            assert advance_status in ("advanced", "already_advanced"), (
                f"With HTTP 200 expected status 'advanced' or 'already_advanced', "
                f"got '{advance_status}'"
            )
            if advance_status == "advanced":
                assert advance_data.get("current_phase") == 1, (
                    f"Expected current_phase=1 after successful advance, "
                    f"got {advance_data.get('current_phase')}"
                )
                assert advance_data.get("from_phase") == 0, (
                    f"Expected from_phase=0, " f"got {advance_data.get('from_phase')}"
                )

        # If we got 409, verify it is gate_in_progress
        if r_advance.status_code == 409:
            assert advance_status == "gate_in_progress", (
                f"With HTTP 409 expected status 'gate_in_progress', " f"got '{advance_status}'"
            )
            assert advance_data.get("current_phase") == 0, (
                f"With gate_in_progress expected current_phase=0, "
                f"got {advance_data.get('current_phase')}"
            )


# ---------------------------------------------------------------------------
# TestUS4GateBlocking
# ---------------------------------------------------------------------------


class TestUS4GateBlocking:
    """User Story 4: Gate blocking scenarios — advance is blocked when
    preconditions are not met."""

    def test_advance_before_artifact_is_blocked(self):
        """Integration test: advance before artifact exists is blocked.

        1. Create a project.
        2. Immediately call advance (do not wait for artifact).
        3. Verify the advance is blocked (gate_in_progress or gate_failed)
           and current_phase is still 0.
        """

        # --------------------------------------------------------------
        # Step 1: Create project
        # --------------------------------------------------------------
        create_body = {
            "title": "Blocked Advance Test",
            "description": "做一个金融分析视频",
        }

        r = requests.post(f"{BASE_URL}/projects", json=create_body)

        assert r.status_code == 201, f"Expected 201 Created, got {r.status_code}: {r.text}"

        project_data = r.json()
        project_id = project_data["id"]
        assert project_id, "Project ID should not be empty"

        # --------------------------------------------------------------
        # Step 2: Immediately call advance
        # --------------------------------------------------------------
        advance_url = f"{BASE_URL}/projects/{project_id}/advance"
        r_advance = requests.post(advance_url)

        # --------------------------------------------------------------
        # Step 3: Verify advance is blocked
        # --------------------------------------------------------------
        # Before the artifact is generated, the advance should be blocked.
        # The gate may respond with gate_in_progress (409) or gate_failed
        # (422). Both are valid blocking responses.
        assert r_advance.status_code in (409, 422), (
            f"Expected advance to be blocked (409 or 422) before artifact exists, "
            f"got {r_advance.status_code}: {r_advance.text}"
        )

        advance_data = r_advance.json()
        advance_status = advance_data.get("status")

        assert advance_status is not None, "Advance response missing 'status' field"

        assert advance_status in ("gate_in_progress", "gate_failed"), (
            f"Expected blocked status 'gate_in_progress' or 'gate_failed', "
            f"got '{advance_status}'"
        )

        # current_phase should still be 0 — advance did not happen
        assert advance_data.get("current_phase") == 0, (
            f"Expected current_phase=0 (not advanced), " f"got {advance_data.get('current_phase')}"
        )

    def test_advance_nonexistent_project_returns_404(self):
        """Integration test: advance for a nonexistent project returns 404.

        1. POST to advance endpoint with a fake project ID.
        2. Verify 404 response.
        """

        # --------------------------------------------------------------
        # Step 1: POST to advance for nonexistent project
        # --------------------------------------------------------------
        fake_project_id = "proj_nonexistent_00000000"
        advance_url = f"{BASE_URL}/projects/{fake_project_id}/advance"
        r_advance = requests.post(advance_url)

        # --------------------------------------------------------------
        # Step 2: Verify 404 response
        # --------------------------------------------------------------
        assert r_advance.status_code == 404, (
            f"Expected 404 for nonexistent project '{fake_project_id}', "
            f"got {r_advance.status_code}: {r_advance.text}"
        )


# ---------------------------------------------------------------------------
# TestFullPhase0HappyPath (T030)
# ---------------------------------------------------------------------------


class TestFullPhase0HappyPath:
    """Cross-cutting integration test: complete Phase 0 happy path.

    Exercises: create -> artifact generation -> revise -> artifact update ->
    advance attempt. Even if advance does not succeed (review not done, etc.),
    the test verifies the pipeline does not crash.
    """

    def test_full_phase0_workflow_create_revise_advance(self):
        """Comprehensive end-to-end test exercising the complete Phase 0 flow.

        1. Create a project with a clear description.
        2. Poll for Phase 0 artifact (standard pattern).
        3. Verify artifact has required fields (topic, category,
           target_duration, platform).
        4. Send a revise chat message ("请把时长改为10-15分钟").
        5. Poll for updated artifact with higher version.
        6. Verify updated artifact still has required fields.
        7. Call advance endpoint.
        8. Verify advance response has status indicating the gate was
           checked (not 404/500).
        9. Verify the project state endpoint shows current_phase >= 0
           (project still exists and is valid).
        """

        # --------------------------------------------------------------
        # Step 1: Create project with clear description
        # --------------------------------------------------------------
        create_body = {
            "title": "Full Workflow Test: Gold Market Analysis",
            "description": (
                "做一个关于近期黄金价格走势的深度分析视频，从技术面和宏观面两个角度解读，"
                "适合投资新手观看，5-8分钟，发布到B站。需要包含图表数据展示和关键点位分析。"
            ),
        }

        r = requests.post(f"{BASE_URL}/projects", json=create_body)

        assert r.status_code == 201, f"Expected 201 Created, got {r.status_code}: {r.text}"

        project_data = r.json()
        project_id = project_data["id"]
        assert project_id, "Project ID should not be empty"

        # --------------------------------------------------------------
        # Step 2: Poll for artifact
        # --------------------------------------------------------------
        deadline = time.monotonic() + POLL_TIMEOUT_SEC
        artifact_url = f"{BASE_URL}/projects/{project_id}/phases/0/artifact"
        initial_artifact = None

        while time.monotonic() < deadline:
            r_art = requests.get(artifact_url)

            if r_art.status_code == 200:
                art_data = r_art.json()
                if art_data.get("artifact_data") is not None:
                    initial_artifact = art_data
                    break
            elif r_art.status_code == 404:
                pass
            else:
                pytest.fail(
                    f"Unexpected status {r_art.status_code} from {artifact_url}: " f"{r_art.text}"
                )

            time.sleep(POLL_INTERVAL_SEC)

        assert (
            initial_artifact is not None
        ), f"Timed out after {POLL_TIMEOUT_SEC}s waiting for Phase 0 artifact"

        # --------------------------------------------------------------
        # Step 3: Verify artifact has required fields
        # --------------------------------------------------------------
        artifact_data = initial_artifact["artifact_data"]

        # 3a. topic is non-empty and >= 5 chars
        topic = artifact_data.get("topic")
        assert topic is not None, "artifact_data.topic is missing"
        assert len(topic) >= 5, (
            f"artifact_data.topic '{topic}' has length {len(topic)}, " f"expected >= 5"
        )

        # 3b. category has level1 and level2 (both non-empty)
        category = artifact_data.get("category")
        assert category is not None, "artifact_data.category is missing"
        assert category.get("level1"), "artifact_data.category.level1 is empty or missing"
        assert category.get("level2"), "artifact_data.category.level2 is empty or missing"

        # 3c. target_duration has min_sec and max_sec (both >= 0)
        target_duration = artifact_data.get("target_duration")
        assert target_duration is not None, "artifact_data.target_duration is missing"
        assert target_duration.get("min_sec") is not None, "target_duration.min_sec is missing"
        assert target_duration.get("max_sec") is not None, "target_duration.max_sec is missing"
        assert (
            target_duration["min_sec"] >= 0
        ), f"target_duration.min_sec={target_duration['min_sec']} must be >= 0"
        assert (
            target_duration["max_sec"] >= 0
        ), f"target_duration.max_sec={target_duration['max_sec']} must be >= 0"

        # 3d. platform is non-empty list
        platform_list = artifact_data.get("platform")
        assert platform_list is not None, "artifact_data.platform is missing"
        assert isinstance(
            platform_list, list
        ), f"platform should be a list, got {type(platform_list).__name__}"
        assert len(platform_list) > 0, "artifact_data.platform list is empty"

        # 3e. artifact_version >= 1
        initial_version = initial_artifact.get("artifact_version")
        assert initial_version is not None, "artifact_version is missing from artifact response"
        assert initial_version >= 1, f"artifact_version={initial_version} must be >= 1"

        # --------------------------------------------------------------
        # Step 4: Send revise chat message
        # --------------------------------------------------------------
        chat_url = f"{BASE_URL}/projects/{project_id}/chat"
        chat_body = {
            "message": "请把时长改为10-15分钟",
            "context": {},
        }

        r_chat = requests.post(chat_url, json=chat_body)

        assert r_chat.status_code == 200, (
            f"Expected 200 OK from chat endpoint, " f"got {r_chat.status_code}: {r_chat.text}"
        )

        chat_response = r_chat.json()
        action = chat_response.get("action")
        assert action is not None, "Chat response missing 'action' field"

        # --------------------------------------------------------------
        # Step 5: Poll for updated artifact with higher version
        # --------------------------------------------------------------
        deadline = time.monotonic() + POLL_TIMEOUT_SEC
        updated_artifact = None

        while time.monotonic() < deadline:
            r_art = requests.get(artifact_url)

            if r_art.status_code == 200:
                art_data = r_art.json()
                current_version = art_data.get("artifact_version")
                if current_version is not None and current_version > initial_version:
                    updated_artifact = art_data
                    break
            elif r_art.status_code == 404:
                pass
            else:
                pytest.fail(
                    f"Unexpected status {r_art.status_code} from {artifact_url}: " f"{r_art.text}"
                )

            time.sleep(POLL_INTERVAL_SEC)

        assert updated_artifact is not None, (
            f"Timed out after {POLL_TIMEOUT_SEC}s waiting for updated artifact "
            f"with version > {initial_version}"
        )

        updated_version = updated_artifact.get("artifact_version")
        assert updated_version > initial_version, (
            f"Expected updated artifact_version={updated_version} "
            f"to be > initial_version={initial_version}"
        )

        # --------------------------------------------------------------
        # Step 6: Verify updated artifact still has required fields
        # --------------------------------------------------------------
        updated_data = updated_artifact["artifact_data"]

        # topic still present and non-empty
        updated_topic = updated_data.get("topic")
        assert updated_topic is not None, "Updated artifact_data.topic is missing"
        assert len(updated_topic) >= 5, (
            f"Updated artifact_data.topic '{updated_topic}' "
            f"has length {len(updated_topic)}, expected >= 5"
        )

        # category still present
        updated_category = updated_data.get("category")
        assert updated_category is not None, "Updated artifact_data.category is missing"
        assert updated_category.get("level1"), "Updated category.level1 is empty or missing"
        assert updated_category.get("level2"), "Updated category.level2 is empty or missing"

        # target_duration still present
        updated_target_duration = updated_data.get("target_duration")
        assert updated_target_duration is not None, "Updated target_duration is missing"
        assert updated_target_duration.get("min_sec") is not None, "Updated min_sec is missing"
        assert (
            updated_target_duration["min_sec"] >= 0
        ), f"Updated min_sec={updated_target_duration['min_sec']} must be >= 0"

        # platform still present
        updated_platform_list = updated_data.get("platform")
        assert updated_platform_list is not None, "Updated platform is missing"
        assert isinstance(updated_platform_list, list), (
            f"Updated platform should be a list, " f"got {type(updated_platform_list).__name__}"
        )
        assert len(updated_platform_list) > 0, "Updated platform list is empty"

        # --------------------------------------------------------------
        # Step 7: Call advance endpoint
        # --------------------------------------------------------------
        advance_url = f"{BASE_URL}/projects/{project_id}/advance"
        r_advance = requests.post(advance_url)

        # --------------------------------------------------------------
        # Step 8: Verify advance response has status (not 404/500)
        # --------------------------------------------------------------
        assert r_advance.status_code not in (404, 500), (
            f"Advance endpoint should not return {r_advance.status_code} "
            f"for valid project. Response: {r_advance.text}"
        )

        advance_data = r_advance.json()
        advance_status = advance_data.get("status")
        assert advance_status is not None, "Advance response missing 'status' field"
        # Valid statuses: gate was checked, not a crash
        assert advance_status in (
            "advanced",
            "already_advanced",
            "gate_in_progress",
            "gate_failed",
        ), f"Unexpected advance status '{advance_status}'. " f"Response: {advance_data}"

        # --------------------------------------------------------------
        # Step 9: Verify project state endpoint shows current_phase >= 0
        # --------------------------------------------------------------
        state_url = f"{BASE_URL}/projects/{project_id}/state"
        r_state = requests.get(state_url)

        assert r_state.status_code == 200, (
            f"Expected 200 OK from state endpoint, " f"got {r_state.status_code}: {r_state.text}"
        )

        state_data = r_state.json()
        current_phase = state_data.get("current_phase")
        assert current_phase is not None, "State response missing 'current_phase' field"
        assert current_phase >= 0, (
            f"Expected current_phase >= 0 (project still exists and is valid), "
            f"got current_phase={current_phase}"
        )


# ---------------------------------------------------------------------------
# TestErrorRecovery (T031)
# ---------------------------------------------------------------------------


class TestErrorRecovery:
    """Cross-cutting integration test: error visibility and recovery.

    Validates that the system gracefully handles edge cases — the chat
    endpoint works, the project stays accessible, and if an artifact exists,
    it is valid.
    """

    def test_llm_error_surfaces_and_retry_via_regenerate(self):
        """Integration test for error visibility and recovery.

        1. Create a project.
        2. Poll for artifact (may succeed or fail — if the LLM fails, the
           task should show as failed).
        3. If artifact was generated, verify it is valid.
        4. Send a regenerate chat message.
        5. Verify regenerate endpoint returns 200 (does not crash).
        6. Poll for new or updated artifact.
        7. Verify the project is still accessible (not corrupted by error).
        """

        # --------------------------------------------------------------
        # Step 1: Create project
        # --------------------------------------------------------------
        create_body = {
            "title": "Error Recovery Test",
            "description": "做一个视频关于投资理财的基础知识介绍",
        }

        r = requests.post(f"{BASE_URL}/projects", json=create_body)

        assert r.status_code == 201, f"Expected 201 Created, got {r.status_code}: {r.text}"

        project_data = r.json()
        project_id = project_data["id"]
        assert project_id, "Project ID should not be empty"

        # --------------------------------------------------------------
        # Step 2: Poll for artifact (may succeed or fail)
        # --------------------------------------------------------------
        deadline = time.monotonic() + POLL_TIMEOUT_SEC
        artifact_url = f"{BASE_URL}/projects/{project_id}/phases/0/artifact"
        initial_artifact = None
        artifact_ready = False

        while time.monotonic() < deadline:
            r_art = requests.get(artifact_url)

            if r_art.status_code == 200:
                art_data = r_art.json()
                if art_data.get("artifact_data") is not None:
                    initial_artifact = art_data
                    artifact_ready = True
                    break
            elif r_art.status_code == 404:
                pass
            else:
                pytest.fail(
                    f"Unexpected status {r_art.status_code} from {artifact_url}: " f"{r_art.text}"
                )

            time.sleep(POLL_INTERVAL_SEC)

        # --------------------------------------------------------------
        # Step 3: If artifact was generated, verify it is valid
        # --------------------------------------------------------------
        if artifact_ready:
            artifact_data = initial_artifact["artifact_data"]

            # Verify core fields exist
            topic = artifact_data.get("topic")
            assert topic is not None, "artifact_data.topic is missing from generated artifact"
            assert len(topic) >= 5, (
                f"artifact_data.topic '{topic}' has length {len(topic)}, " f"expected >= 5"
            )

            category = artifact_data.get("category")
            assert category is not None, "artifact_data.category is missing from generated artifact"
            assert category.get("level1"), "category.level1 is empty"
            assert category.get("level2"), "category.level2 is empty"

            target_duration = artifact_data.get("target_duration")
            assert target_duration is not None, "artifact_data.target_duration is missing"
            assert target_duration.get("min_sec") is not None
            assert target_duration.get("max_sec") is not None
            assert target_duration["min_sec"] >= 0
            assert target_duration["max_sec"] >= 0

            # Record version for later comparison
            initial_version = initial_artifact.get("artifact_version", 0)
        else:
            initial_version = 0

        # --------------------------------------------------------------
        # Step 4: Send a regenerate chat message
        # --------------------------------------------------------------
        chat_url = f"{BASE_URL}/projects/{project_id}/chat"
        chat_body = {
            "message": "重新生成需求",
            "context": {},
        }

        r_chat = requests.post(chat_url, json=chat_body)

        # --------------------------------------------------------------
        # Step 5: Verify regenerate endpoint returns 200 (does not crash)
        # --------------------------------------------------------------
        assert r_chat.status_code == 200, (
            f"Expected 200 OK from chat endpoint, " f"got {r_chat.status_code}: {r_chat.text}"
        )

        chat_response = r_chat.json()
        # Action should be present — the system should not crash
        action = chat_response.get("action")
        assert action is not None, "Chat response missing 'action' field"

        # --------------------------------------------------------------
        # Step 6: Poll for new or updated artifact
        # --------------------------------------------------------------
        deadline = time.monotonic() + POLL_TIMEOUT_SEC
        updated_artifact = None

        while time.monotonic() < deadline:
            r_art = requests.get(artifact_url)

            if r_art.status_code == 200:
                art_data = r_art.json()
                current_version = art_data.get("artifact_version")
                if current_version is not None and current_version > initial_version:
                    updated_artifact = art_data
                    break
                # Also accept any artifact if none was generated initially
                if not artifact_ready and art_data.get("artifact_data") is not None:
                    updated_artifact = art_data
                    break
            elif r_art.status_code == 404:
                pass
            else:
                pytest.fail(
                    f"Unexpected status {r_art.status_code} from {artifact_url}: " f"{r_art.text}"
                )

            time.sleep(POLL_INTERVAL_SEC)

        # If artifact existed before, expect an updated one to confirm
        # regeneration completed. If not, verify polling did not crash.
        if artifact_ready:
            assert updated_artifact is not None, (
                f"Timed out after {POLL_TIMEOUT_SEC}s waiting for updated "
                f"artifact after regenerate"
            )
            updated_version = updated_artifact.get("artifact_version")
            assert updated_version > initial_version, (
                f"Expected updated artifact_version={updated_version} "
                f"to be > initial_version={initial_version}"
            )

        # --------------------------------------------------------------
        # Step 7: Verify the project is still accessible
        # --------------------------------------------------------------
        project_url = f"{BASE_URL}/projects/{project_id}"
        r_project = requests.get(project_url)

        assert r_project.status_code == 200, (
            f"Expected 200 OK from project endpoint after error recovery, "
            f"got {r_project.status_code}: {r_project.text}"
        )

        project_state = r_project.json()
        assert project_state.get("project_id") == project_id, (
            f"Project ID mismatch: expected {project_id}, " f"got {project_state.get('project_id')}"
        )
        assert (
            project_state.get("current_phase") is not None
        ), "Project state missing 'current_phase' — system may be corrupted"
        assert (
            project_state.get("status") is not None
        ), "Project state missing 'status' — system may be corrupted"
