"""[SPEC-C-102] Integration tests for /preferences/writeback-suggestions.

Authority: docs/specs/SPEC-C-backend-core.md §C-BDD-3.
Task card: tasks/SPEC-C/C-102-preference-extractor-writeback.md.

Boots a FastAPI app with the writeback router, fires a POST and
verifies the full request/response cycle end-to-end. Complements the
unit-level assertions in tests/unit/backend-core/test_spec_c_102.py.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.backend.api.preferences import router


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_writeback_suggestions_endpoint_returns_three_categories() -> None:
    client = _client()
    body = {
        "project_id": "proj_1",
        "phase": "P4_tts",
        "current_settings": {
            "tts.rate": 1.0,
            "tts.voice": "bob",
            "tts.pitch": 0.9,
        },
        "historical_preferences": [
            {
                "preference_id": "pref_keep",
                "scope": "stage",
                "stage": "P4_tts",
                "key": "tts.rate",
                "value": 1.0,
                "source": "user_explicit",
                "applies_to_artifacts": [],
                "created_at": "2026-04-24T00:00:00Z",
            },
            {
                "preference_id": "pref_update",
                "scope": "stage",
                "stage": "P4_tts",
                "key": "tts.voice",
                "value": "alice",
                "source": "user_explicit",
                "applies_to_artifacts": [],
                "created_at": "2026-04-24T00:00:00Z",
            },
        ],
        "confidence": 0.9,
    }

    r = client.post("/preferences/writeback-suggestions", json=body)
    assert r.status_code == 200, r.text
    suggestions = r.json()["suggestions"]
    actions = {s["key"]: s["recommended_action"] for s in suggestions}
    assert actions["tts.rate"] == "keep"
    assert actions["tts.voice"] == "update"
    assert actions["tts.pitch"] == "add_stage_override"

    # confidence=0.9 > 0.85 -> update/add_stage_override proposed_action=auto_save,
    # keep falls through to ask_writeback (per service contract).
    by_key = {s["key"]: s for s in suggestions}
    assert by_key["tts.voice"]["proposed_action"] == "auto_save"
    assert by_key["tts.pitch"]["proposed_action"] == "auto_save"
    assert by_key["tts.rate"]["proposed_action"] == "ask_writeback"


def test_writeback_suggestions_endpoint_rejects_invalid_body() -> None:
    client = _client()
    # Missing required project_id.
    r = client.post(
        "/preferences/writeback-suggestions",
        json={"phase": "P4_tts", "current_settings": {}},
    )
    assert r.status_code == 422


def test_writeback_suggestions_endpoint_low_confidence_ask_writeback() -> None:
    """Confidence <= 0.85 -> proposed_action='ask_writeback' even for update."""
    client = _client()
    r = client.post(
        "/preferences/writeback-suggestions",
        json={
            "project_id": "proj_1",
            "phase": "P4_tts",
            "current_settings": {"tts.rate": 1.2},
            "historical_preferences": [
                {
                    "preference_id": "pref_x",
                    "scope": "stage",
                    "stage": "P4_tts",
                    "key": "tts.rate",
                    "value": 1.0,
                    "source": "user_explicit",
                    "applies_to_artifacts": [],
                    "created_at": "2026-04-24T00:00:00Z",
                }
            ],
            "confidence": 0.70,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["suggestions"][0]["recommended_action"] == "update"
    assert body["suggestions"][0]["proposed_action"] == "ask_writeback"
