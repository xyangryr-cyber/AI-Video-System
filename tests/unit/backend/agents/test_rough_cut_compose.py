"""[SPEC-D-008] Tests for RoughCutAgent.compose() — Remotion rough cut composition.

Verifies: output path, audio source priority (P6 > P4), subtitle track params,
ffprobe-measured duration.
"""

from __future__ import annotations

import json
import os
from unittest import mock

from src.backend.agents.rough_cut_agent import RoughCutAgent


# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

def _make_storyboard() -> list[dict]:
    return [
        {
            "shot_id": "s1",
            "type": "keyframe",
            "time_range": {"start_seconds": 0.0, "end_seconds": 5.0},
        },
        {
            "shot_id": "s2",
            "type": "broll",
            "time_range": {"start_seconds": 5.0, "end_seconds": 10.0},
        },
    ]


def _make_timeline() -> dict:
    return {"total_duration_sec": 10.0, "segments": []}


def _make_keyframe_renders() -> list[dict]:
    return [
        {"shot_id": "s1", "render_path": "phase_8/seg_01.mp4"},
    ]


def _make_polished_script() -> dict:
    return {
        "segments": [
            {
                "segment_id": "seg_01",
                "text": "Today we analyze the market trends.",
                "start_seconds": 0.0,
                "end_seconds": 5.0,
            },
        ],
    }


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------

def _fake_ffmpeg_success(cmd, capture_output=False, timeout=300, **kwargs):
    """Return a successful subprocess.CompletedProcess."""
    return mock.Mock(returncode=0, stdout=b"", stderr=b"")


def _fake_ffprobe_output(cmd, capture_output=False, timeout=30, **kwargs):
    """Return ffprobe JSON with a 10-second duration."""
    out = json.dumps({"format": {"duration": "10.000000"}}).encode()
    return mock.Mock(returncode=0, stdout=out, stderr=b"")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRoughCutComposeOutputPath:
    def test_output_path_is_rough_cut_v1_mp4(self):
        """compose() returns phase_10/rough_cut_v1.mp4 as the output path."""
        result = RoughCutAgent.compose(
            project_id="proj_test",
            storyboard=_make_storyboard(),
            timeline=_make_timeline(),
            keyframe_renders=_make_keyframe_renders(),
        )
        assert result["rough_cut_path"] == "phase_10/rough_cut_v1.mp4"

    def test_output_path_is_relative_to_project(self):
        """compose() returns a relative path within the project structure."""
        result = RoughCutAgent.compose(
            project_id="proj_abc",
            storyboard=_make_storyboard(),
            timeline=_make_timeline(),
            keyframe_renders=_make_keyframe_renders(),
        )
        assert result["rough_cut_path"].startswith("phase_10/")
        assert result["rough_cut_path"].endswith("rough_cut_v1.mp4")


class TestRoughCutComposeAudioSource:
    def test_uses_p6_audio_when_exists(self):
        """When P6 final_audio_with_bgm_sfx.mp3 exists, use it as primary audio."""
        with mock.patch.object(os.path, "isfile", return_value=True):
            result = RoughCutAgent.compose(
                project_id="proj_test",
                storyboard=_make_storyboard(),
                timeline=_make_timeline(),
                keyframe_renders=_make_keyframe_renders(),
            )
        assert result["audio_source"] == "phase_6/final_audio_with_bgm_sfx.mp3"

    def test_falls_back_to_p4_when_p6_missing(self):
        """When P6 audio is missing, fallback to P4 narration_master.mp3."""

        def isfile_side_effect(path):
            # P6 audio missing, P4 audio exists
            return "phase_6" not in path

        with mock.patch.object(os.path, "isfile", side_effect=isfile_side_effect):
            result = RoughCutAgent.compose(
                project_id="proj_test",
                storyboard=_make_storyboard(),
                timeline=_make_timeline(),
                keyframe_renders=_make_keyframe_renders(),
            )
        assert result["audio_source"] == "phase_4/narration_master.mp3"

    def test_audio_source_none_when_neither_exists(self):
        """When neither P6 nor P4 audio exists, audio_source is None."""

        with mock.patch.object(os.path, "isfile", return_value=False):
            result = RoughCutAgent.compose(
                project_id="proj_test",
                storyboard=_make_storyboard(),
                timeline=_make_timeline(),
                keyframe_renders=_make_keyframe_renders(),
            )
        assert result["audio_source"] is None


class TestRoughCutComposeSubtitleTrack:
    def test_subtitle_track_params_in_output(self):
        """compose() returns a subtitle_path pointing to the generated SRT."""
        with mock.patch.object(os.path, "isfile", return_value=False):
            result = RoughCutAgent.compose(
                project_id="proj_test",
                storyboard=_make_storyboard(),
                timeline=_make_timeline(),
                keyframe_renders=_make_keyframe_renders(),
                polished_script=_make_polished_script(),
            )
        assert "subtitle_path" in result
        assert result["subtitle_path"] == "phase_10/subtitle.srt"
        assert "subtitle_track" in result
        assert result["subtitle_track"] is True

    def test_subtitle_disabled_when_no_polished_script(self):
        """When polished_script is not provided, subtitle_track is False."""
        with mock.patch.object(os.path, "isfile", return_value=False):
            result = RoughCutAgent.compose(
                project_id="proj_test",
                storyboard=_make_storyboard(),
                timeline=_make_timeline(),
                keyframe_renders=_make_keyframe_renders(),
            )
        assert result["subtitle_track"] is False
        assert "subtitle_path" not in result


class TestRoughCutComposeDuration:
    def test_duration_comes_from_timeline_when_no_ffprobe(self):
        """When ffprobe is not available, duration falls back to timeline total."""
        with mock.patch.object(os.path, "isfile", return_value=False):
            result = RoughCutAgent.compose(
                project_id="proj_test",
                storyboard=_make_storyboard(),
                timeline=_make_timeline(),
                keyframe_renders=_make_keyframe_renders(),
            )
        assert result["duration_seconds"] == 10.0  # from timeline

    def test_duration_prefers_ffprobe_when_file_exists(self):
        """When the output file already exists, use ffprobe-measured duration."""

        def isfile_side_effect(path):
            if "rough_cut_v1.mp4" in path:
                return True
            return False

        with mock.patch.object(os.path, "isfile", side_effect=isfile_side_effect):
            with mock.patch("subprocess.run", side_effect=_fake_ffprobe_output):
                result = RoughCutAgent.compose(
                    project_id="proj_test",
                    storyboard=_make_storyboard(),
                    timeline=_make_timeline(),
                    keyframe_renders=_make_keyframe_renders(),
                )
        assert result["duration_seconds"] == 10.0  # from ffprobe


class TestRoughCutComposeMetadata:
    def test_returns_expected_metadata_keys(self):
        """compose() output includes resolution, fps, codec metadata."""
        with mock.patch.object(os.path, "isfile", return_value=False):
            result = RoughCutAgent.compose(
                project_id="proj_test",
                storyboard=_make_storyboard(),
                timeline=_make_timeline(),
                keyframe_renders=_make_keyframe_renders(),
            )
        assert result["resolution"] == "1920x1080"
        assert result["fps"] == 30
        assert result["codec"] == "h264"
        assert "target_bitrate" in result

    def test_transitions_applied(self):
        """compose() records transition effects in output."""
        with mock.patch.object(os.path, "isfile", return_value=False):
            result = RoughCutAgent.compose(
                project_id="proj_test",
                storyboard=_make_storyboard(),
                timeline=_make_timeline(),
                keyframe_renders=_make_keyframe_renders(),
                transitions=[
                    {"type": "crossfade", "duration_seconds": 0.5},
                    {"type": "hard_cut", "duration_seconds": 0.0},
                ],
            )
        assert "transitions" in result
        assert len(result["transitions"]) == 2
        assert result["transitions"][0]["type"] == "crossfade"
        assert result["transitions"][0]["applied"] is True
