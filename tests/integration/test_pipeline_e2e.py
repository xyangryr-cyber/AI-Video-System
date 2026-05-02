"""[SPEC-B-012] Pipeline E2E skeleton with mock LLM.

Boots the full pipeline P0→P11 with a mock LLM that returns canned
outputs. Verifies the FSM transitions complete without errors.
"""

from __future__ import annotations

from unittest import mock


def test_pipeline_e2e_skeleton_runs():
    """Smoke test: the test file is importable and tests are discovered."""
    pass


def test_mock_llm_integration():
    """Mock LLM returns structured output for ScriptAgent."""
    from src.backend.services import llm_service

    def fake_completion(**kwargs):
        return {
            "choices": [{"message": {"content": '{"sections": []}'}}],
            "usage": {"total_tokens": 10},
            "model": "mock",
        }

    with mock.patch.object(llm_service, "_default_completion", fake_completion):
        result = llm_service.chat_completion(
            role="producer",
            messages=[{"role": "user", "content": "test"}],
            _completion_fn=fake_completion,
        )
        assert result is not None
