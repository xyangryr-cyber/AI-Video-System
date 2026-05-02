"""Tests for [SPEC-F-NNN] P10 Rough Cut — consume .mp4 segments.

Authority: 0429第二轮remotion开发任务.md Task 5.

Test strategy:
- AC-1: When phase_8/*.mp4 files exist, use FFmpeg concat with -c:v copy
- AC-2: When no .mp4 files, fall back to PNG path
- AC-3: Audio is mixed in (narration_master.mp3)
"""

from __future__ import annotations

import json
import os
import sqlite3
from unittest import mock


def _make_storyboard(shots: list[dict]) -> dict:
    return {"shots": shots}


def _make_shot(shot_id: str, start: float, end: float) -> dict:
    return {
        "shot_id": shot_id,
        "type": "template",
        "template_type": "animated_line_chart",
        "content": {"title": "Test"},
        "time_range": {"start_seconds": start, "end_seconds": end},
    }


class TestP10Mp4Concat:
    """Unit tests for _execute_rough_cut_agent() with .mp4 segments."""

    def _import_fn(self):
        from src.backend.api.routes.projects import _execute_rough_cut_agent
        return _execute_rough_cut_agent

    def _mock_open_storyboard(self, shots: list[dict]):
        real_open = open
        storyboard_json = json.dumps(_make_storyboard(shots))

        def _side_effect(file, mode="r", *args, **kwargs):
            file_str = str(file)
            if "storyboard.json" in file_str:
                return mock.mock_open(read_data=storyboard_json).return_value
            if "narration.json" in file_str:
                return mock.mock_open(read_data="{}").return_value
            if "concat_list.txt" in file_str and "w" in str(mode):
                return mock.mock_open().return_value
            return real_open(file, mode, *args, **kwargs)

        return mock.patch("builtins.open", side_effect=_side_effect)

    def test_mp4_files_use_copy_codec(self):
        """AC-1: When .mp4 files exist, FFmpeg uses -c:v copy."""
        shots = [
            _make_shot("shot_01", 0, 15),
            _make_shot("shot_02", 15, 30),
        ]

        with self._mock_open_storyboard(shots):
            with mock.patch("os.makedirs"):
                # Simulate: phase_8 has .mp4 files
                def _listdir_side_effect(path):
                    if "phase_8" in str(path):
                        return ["shot_01.mp4", "shot_02.mp4"]
                    return []

                with mock.patch("os.listdir", side_effect=_listdir_side_effect):
                    with mock.patch("os.path.isdir", return_value=True):
                        with mock.patch("os.path.isfile", return_value=True):
                            with mock.patch("os.path.exists", return_value=False):
                                with mock.patch("subprocess.run") as mock_run:
                                    mock_run.return_value = mock.Mock(
                                        returncode=0, stdout="", stderr=""
                                    )
                                    with mock.patch("os.remove"):
                                        with mock.patch("shutil.which", return_value="/usr/local/bin/ffmpeg"):
                                            fn = self._import_fn()
                                            db = sqlite3.connect(":memory:")
                                            result = fn(db, "test-p10", "Title", "Desc")

            # Verify FFmpeg was called
            assert mock_run.called
            call_args = mock_run.call_args[0][0]

            # Should use -c:v copy for lossless concat
            assert "-c:v" in call_args
            copy_idx = call_args.index("-c:v")
            assert call_args[copy_idx + 1] == "copy"

            # Should NOT use libx264 (which would re-encode)
            assert "libx264" not in call_args

            # Result should have the expected fields
            assert result["resolution"] == "1920x1080"
            assert result["fps"] == 30

    def test_fallback_to_png_when_no_mp4(self):
        """AC-2: When no .mp4 files, fall back to PNG path with libx264."""
        shots = [_make_shot("shot_01", 0, 10)]

        with self._mock_open_storyboard(shots):
            with mock.patch("os.makedirs"):
                # Simulate: phase_8 has only .png files
                def _listdir_side_effect(path):
                    if "phase_8" in str(path):
                        return ["shot_01.png"]
                    return []

                with mock.patch("os.listdir", side_effect=_listdir_side_effect):
                    with mock.patch("os.path.isdir", return_value=True):
                        with mock.patch("os.path.isfile", return_value=True):
                            with mock.patch("os.path.exists", return_value=False):
                                with mock.patch("subprocess.run") as mock_run:
                                    mock_run.return_value = mock.Mock(
                                        returncode=0, stdout="", stderr=""
                                    )
                                    with mock.patch("os.remove"):
                                        with mock.patch("shutil.which", return_value="/usr/local/bin/ffmpeg"):
                                            fn = self._import_fn()
                                            db = sqlite3.connect(":memory:")
                                            fn(db, "test-p10", "Title", "Desc")

            call_args = mock_run.call_args[0][0]
            # PNG path should still use libx264 (re-encode)
            assert "libx264" in call_args
