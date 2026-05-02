"""[SPEC-F-014] Tests for keyframe render uniform color frame detection."""

from __future__ import annotations

from unittest.mock import patch

from PIL import Image, ImageDraw

from src.backend.agents.keyframe_render_agent import (
    KeyframeRenderAgent,
    _is_uniform_color_frame,
)


# ------------------------------------------------------------------
# Helper to create test images
# ------------------------------------------------------------------


def _create_solid_image(path: str, size: tuple = (100, 100), color: str = "#1a1a1a") -> None:
    """Create a solid-color PNG at the given path."""
    img = Image.new("RGB", size, color=color)
    img.save(path, "PNG")


def _create_non_uniform_image(path: str, size: tuple = (100, 100)) -> None:
    """Create a non-uniform PNG with a colored rectangle at the given path."""
    img = Image.new("RGB", size, color="#1a1a1a")
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 80, 80], fill="#ffffff")
    img.save(path, "PNG")


# ------------------------------------------------------------------
# Test 1: _is_uniform_color_frame returns True for solid color
# ------------------------------------------------------------------


def test_is_uniform_color_frame_solid(tmp_path):
    """A solid-color PNG should be detected as uniform."""
    solid_path = tmp_path / "solid.png"
    _create_solid_image(str(solid_path))

    result = _is_uniform_color_frame(str(solid_path))
    assert result is True


# ------------------------------------------------------------------
# Test 2: _is_uniform_color_frame returns False for non-uniform
# ------------------------------------------------------------------


def test_is_uniform_color_frame_non_uniform(tmp_path):
    """A PNG with content should NOT be detected as uniform."""
    non_uniform_path = tmp_path / "non_uniform.png"
    _create_non_uniform_image(str(non_uniform_path))

    result = _is_uniform_color_frame(str(non_uniform_path))
    assert result is False


# ------------------------------------------------------------------
# Test 3: render_with_degradation detects uniform output
# ------------------------------------------------------------------


def test_render_with_degradation_detects_uniform(tmp_path):
    """render_with_degradation returns error_code='render_failed' when output is uniform."""
    solid_path = tmp_path / "uniform.png"
    _create_solid_image(str(solid_path))

    agent = KeyframeRenderAgent()
    mock_response = {
        "shot_id": "shot_01",
        "render_path": str(solid_path),
        "engine": "pillow",
    }

    with patch.object(agent, "_execute_render", return_value=mock_response):
        result = agent.render_with_degradation(
            shot_id="shot_01",
            template_type="text_card",
            material_url="phase_7a/test.png",
        )

    assert result["error_code"] == "render_failed"
    assert result["render_path"] == str(solid_path)


# ------------------------------------------------------------------
# Test 4: render_with_degradation allows non-uniform output
# ------------------------------------------------------------------


def test_render_with_degradation_allows_non_uniform(tmp_path):
    """render_with_degradation returns error_code=None when output is non-uniform."""
    non_uniform_path = tmp_path / "non_uniform.png"
    _create_non_uniform_image(str(non_uniform_path))

    agent = KeyframeRenderAgent()
    mock_response = {
        "shot_id": "shot_02",
        "render_path": str(non_uniform_path),
        "engine": "pillow",
    }

    with patch.object(agent, "_execute_render", return_value=mock_response):
        result = agent.render_with_degradation(
            shot_id="shot_02",
            template_type="text_card",
            material_url="phase_7a/test.png",
        )

    assert result["error_code"] is None
    assert result["render_path"] == str(non_uniform_path)
