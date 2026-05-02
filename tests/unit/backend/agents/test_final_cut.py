"""[SPEC-D-009] Tests for FinalCutAgent.adjust() — platform transcoding, cover generation, SRT export.

Verifies: 3 distinct output paths (bilibili/douyin/SRT), cover generation (3 PNGs),
douyin vertical dimensions (1080x1920), download_urls correctness.
"""

from __future__ import annotations

import os
from unittest import mock

from src.backend.agents.final_cut_agent import FinalCutAgent


# ---------------------------------------------------------------------------
# Tests — output paths and download_urls
# ---------------------------------------------------------------------------


class TestFinalCutOutputPaths:
    def test_three_output_paths_are_distinct(self):
        """bilibili, douyin, and SRT outputs have different paths."""
        result = FinalCutAgent.adjust(
            project_id="proj_test",
            rough_cut_path="phase_10/rough_cut_v1.mp4",
        )
        urls = result["download_urls"]
        assert urls["bilibili"] != urls["douyin"], "bilibili and douyin should differ"
        assert urls["bilibili"] != urls["srt"], "bilibili and srt should differ"
        assert urls["douyin"] != urls["srt"], "douyin and srt should differ"

    def test_bilibili_path_is_correct(self):
        """Bilibili output points to phase_11/final_bilibili_1080p.mp4."""
        result = FinalCutAgent.adjust(
            project_id="proj_test",
            rough_cut_path="phase_10/rough_cut_v1.mp4",
        )
        assert "final_bilibili_1080p.mp4" in result["download_urls"]["bilibili"]

    def test_douyin_path_is_correct(self):
        """Douyin output points to phase_11/final_douyin_vertical.mp4."""
        result = FinalCutAgent.adjust(
            project_id="proj_test",
            rough_cut_path="phase_10/rough_cut_v1.mp4",
        )
        assert "final_douyin_vertical.mp4" in result["download_urls"]["douyin"]

    def test_srt_path_is_correct(self):
        """SRT output points to phase_11/subtitle.srt."""
        result = FinalCutAgent.adjust(
            project_id="proj_test",
            rough_cut_path="phase_10/rough_cut_v1.mp4",
        )
        assert "subtitle.srt" in result["download_urls"]["srt"]

    def test_download_urls_use_api_prefix(self):
        """download_urls follow /api/projects/{id}/files/... pattern."""
        result = FinalCutAgent.adjust(
            project_id="proj_abc123",
            rough_cut_path="phase_10/rough_cut_v1.mp4",
        )
        for key in ("bilibili", "douyin", "srt"):
            url = result["download_urls"][key]
            assert url.startswith("/api/projects/proj_abc123/files/"), (
                f"{key} URL missing project prefix: {url}"
            )


# ---------------------------------------------------------------------------
# Tests — platform dimensions
# ---------------------------------------------------------------------------


class TestFinalCutPlatformDimensions:
    def test_douyin_output_is_vertical_1080x1920(self):
        """Douyin video params specify 1080x1920 (vertical 9:16)."""
        result = FinalCutAgent.adjust(
            project_id="proj_test",
            rough_cut_path="phase_10/rough_cut_v1.mp4",
        )
        douyin_params = result["platform_params"]["douyin"]
        assert douyin_params["width"] == 1080
        assert douyin_params["height"] == 1920

    def test_bilibili_output_is_horizontal_1920x1080(self):
        """Bilibili video params specify 1920x1080 (horizontal 16:9)."""
        result = FinalCutAgent.adjust(
            project_id="proj_test",
            rough_cut_path="phase_10/rough_cut_v1.mp4",
        )
        bilibili_params = result["platform_params"]["bilibili"]
        assert bilibili_params["width"] == 1920
        assert bilibili_params["height"] == 1080

    def test_douyin_bitrate_lower_than_bilibili(self):
        """Douyin uses 6Mbps vs bilibili 8Mbps target bitrate."""
        result = FinalCutAgent.adjust(
            project_id="proj_test",
            rough_cut_path="phase_10/rough_cut_v1.mp4",
        )
        bili = result["platform_params"]["bilibili"]
        douy = result["platform_params"]["douyin"]
        assert bili["bitrate"] == "8M"
        assert douy["bitrate"] == "6M"


# ---------------------------------------------------------------------------
# Tests — cover generation
# ---------------------------------------------------------------------------


class TestFinalCutCoverGeneration:
    def test_cover_generation_creates_three_pngs(self):
        """adjust() returns 3 cover image paths."""
        result = FinalCutAgent.adjust(
            project_id="proj_test",
            rough_cut_path="phase_10/rough_cut_v1.mp4",
            title="Market Analysis 2026",
        )
        assert "cover_paths" in result
        assert len(result["cover_paths"]) == 3

    def test_cover_variants_are_named_correctly(self):
        """Three cover variants: character_dominant, title_focused, data_highlight."""
        result = FinalCutAgent.adjust(
            project_id="proj_test",
            rough_cut_path="phase_10/rough_cut_v1.mp4",
        )
        names = [os.path.basename(p) for p in result["cover_paths"]]
        assert "cover_character_dominant.png" in names
        assert "cover_title_focused.png" in names
        assert "cover_data_highlight.png" in names

    def test_cover_dimensions_match_bilibili_spec(self):
        """Cover images use bilibili spec: 1146x717."""
        result = FinalCutAgent.adjust(
            project_id="proj_test",
            rough_cut_path="phase_10/rough_cut_v1.mp4",
        )
        assert result["cover_dimensions"] == {"width": 1146, "height": 717}

    def test_cover_generation_called_even_without_title(self):
        """Cover PNGs are still generated when title is empty."""
        result = FinalCutAgent.adjust(
            project_id="proj_test",
            rough_cut_path="phase_10/rough_cut_v1.mp4",
        )
        assert len(result["cover_paths"]) == 3


# ---------------------------------------------------------------------------
# Tests — adjustments metadata
# ---------------------------------------------------------------------------


class TestFinalCutAdjustments:
    def test_adjustments_recorded_in_output(self):
        """adjust() records which fine-cut adjustments were applied."""
        result = FinalCutAgent.adjust(
            project_id="proj_test",
            rough_cut_path="phase_10/rough_cut_v1.mp4",
            adjustments={"intro_outro": True, "volume_normalize": True},
        )
        assert "adjustments_applied" in result
        assert "intro_outro" in result["adjustments_applied"]
        assert "volume_normalize" in result["adjustments_applied"]

    def test_platform_outputs_listed(self):
        """result['platform_outputs'] lists each platform file path."""
        result = FinalCutAgent.adjust(
            project_id="proj_test",
            rough_cut_path="phase_10/rough_cut_v1.mp4",
        )
        assert "platform_outputs" in result
        paths = result["platform_outputs"]
        assert any("final_bilibili_1080p.mp4" in p for p in paths)
        assert any("final_douyin_vertical.mp4" in p for p in paths)
