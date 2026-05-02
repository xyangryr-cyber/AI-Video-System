"""Tests for [SPEC-F-014] KeyframeRenderAgent degradation + error_code + prompt constraints."""

import time
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class OutboundBlockedException(Exception):
    """Raised when an outbound request targets a non-whitelisted host."""


class TestAC1:
    """AC-1: mock render exception -> error_code='render_failed' + default text card path"""

    def test_render_exception_yields_text_card(self):
        from src.backend.agents.keyframe_render_agent import KeyframeRenderAgent

        agent = KeyframeRenderAgent()

        # Mock _execute_render to simulate a Remotion render failure
        with patch.object(
            agent, "_execute_render", side_effect=RuntimeError("Remotion render failed")
        ):
            result = agent.render_with_degradation(
                shot_id="shot_001",
                template_type="chart_card",
            )

        assert result is not None, (
            "render_with_degradation must return a result even on failure"
        )
        assert result.get("error_code") == "render_failed", (
            f"expected error_code='render_failed', got {result.get('error_code')}"
        )
        assert "render_path" in result, (
            "must include a render_path for the fallback text card"
        )
        assert "fallback" in result.get(
            "render_path", ""
        ).lower() or "text_card" in result.get("render_path", ""), (
            "render_path must point to a default text card"
        )


class TestAC2:
    """AC-2: material file missing -> error_code='material_missing', no artifact"""

    def test_material_missing_no_artifact(self):
        from src.backend.agents.keyframe_render_agent import KeyframeRenderAgent

        agent = KeyframeRenderAgent()

        result = agent.check_material_readiness(
            material_path="/nonexistent/path/material.png",
            shot_id="shot_002",
        )

        assert result["error_code"] == "material_missing", (
            f"expected error_code='material_missing', got {result.get('error_code')}"
        )
        assert (
            result.get("artifact_path") is None or result.get("artifact_path") == ""
        ), "material_missing must produce no artifact"


class TestAC3:
    """AC-3: material unverified (status != verified) -> error_code='material_unverified'"""

    def test_material_unverified_defensive_path(self):
        from src.backend.agents.keyframe_render_agent import KeyframeRenderAgent

        agent = KeyframeRenderAgent()

        # Defensive check: even if ReadinessCheck missed it, render agent catches unverified material
        result = agent.check_material_readiness(
            material_path="/tmp/test_material.png",
            shot_id="shot_003",
            material_status="pending",  # not verified
        )

        assert result["error_code"] == "material_unverified", (
            f"expected error_code='material_unverified', got {result.get('error_code')}"
        )


class TestAC4:
    """AC-4: non-whitelist host -> OutboundBlockedException -> error_code='render_failed'"""

    def test_outbound_blocked_reported_as_render_failed(self):
        from src.backend.agents.keyframe_render_agent import KeyframeRenderAgent

        agent = KeyframeRenderAgent()

        # Simulate outbound call to non-whitelisted host
        with patch.object(
            agent,
            "_execute_render",
            side_effect=OutboundBlockedException("host not in whitelist: evil.com"),
        ):
            result = agent.render_with_degradation(
                shot_id="shot_004",
                template_type="chart_card",
            )

        assert result["error_code"] == "render_failed", (
            f"OutboundBlockedException must be reported as render_failed, got {result.get('error_code')}"
        )


class TestAC5:
    """AC-5: default text card renders in < 2s (CI benchmark)"""

    def test_text_card_under_2s(self):
        from src.backend.render.default_text_card import render_default_text_card

        start = time.perf_counter()
        result = render_default_text_card(
            shot_id="perf_test_shot",
            text="Default fallback content for performance benchmark.",
        )
        elapsed = time.perf_counter() - start

        assert result is not None, "render_default_text_card must return a result"
        assert "path" in result or "render_path" in result, "result must include a path"
        assert elapsed < 2.0, (
            f"default text card render took {elapsed:.3f}s, must be < 2.0s"
        )


class TestAC6:
    """AC-6: every render_result must carry error_code; missing -> MalformedRenderResultError"""

    def test_render_result_error_code_required(self):
        from src.backend.render.render_result import (
            validate_render_result,
            MalformedRenderResultError,
        )

        # Success case: error_code=null is valid
        valid = {"shot_id": "s1", "render_path": "/tmp/out.png", "error_code": None}
        validate_render_result(valid)  # must not raise

        # Missing error_code entirely
        invalid = {"shot_id": "s2", "render_path": "/tmp/out2.png"}
        with pytest.raises(MalformedRenderResultError, match="error_code"):
            validate_render_result(invalid)

    def test_success_result_error_code_is_null(self):
        from src.backend.render.render_result import (
            validate_render_result,
        )

        valid = {"shot_id": "s3", "render_path": "/tmp/out3.png", "error_code": None}
        validate_render_result(valid)  # must not raise


class TestAC7:
    """AC-7: prompt hard constraint — external URL in LLM output -> blocked, no request"""

    def test_prompt_hard_constraint_outbound_blocked(self):
        from src.backend.agents.keyframe_render_agent import KeyframeRenderAgent

        agent = KeyframeRenderAgent()

        # Mock LLM returning a URL outside phase_7a/
        external_url = "https://evil.com/malicious.png"
        mock_llm_response = f'{{"material_url": "{external_url}"}}'

        # The agent must detect external URL and block before making outbound request
        with patch.object(
            agent,
            "_call_llm",
            return_value=mock_llm_response,
        ):
            result = agent.render_with_degradation(
                shot_id="shot_007",
                template_type="chart_card",
            )

        # Must not have initiated an outbound request to external URL
        assert result["error_code"] is not None, (
            "external URL must trigger an error code"
        )
        assert result["error_code"] == "render_failed", (
            f"expected render_failed for blocked external URL, got {result.get('error_code')}"
        )
