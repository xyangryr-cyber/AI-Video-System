"""Tests for [SPEC-F-NNN] P8 Remotion render pipeline.

Authority: 0429第二轮remotion开发任务.md Task 4.

Test strategy:
- AC-1: Template shots call Node.js subprocess via subprocess.run
- AC-2: Pillow fallback triggers when Node is unavailable
- AC-3: BRoll shots are skipped (render_path=None)
- AC-4: Node render failure falls through to Pillow fallback
"""

from __future__ import annotations

import json
import os
import sqlite3
from unittest import mock


def _make_storyboard(shots: list[dict]) -> dict:
    return {"shots": shots}


def _make_template_shot(
    shot_id: str = "shot_01",
    template_type: str = "animated_line_chart",
    content: dict | None = None,
    start_seconds: float = 0,
    end_seconds: float = 10,
) -> dict:
    return {
        "shot_id": shot_id,
        "type": "template",
        "template_type": template_type,
        "content": content or {"title": "Test"},
        "time_range": {
            "start_seconds": start_seconds,
            "end_seconds": end_seconds,
        },
    }


def _make_broll_shot(shot_id: str = "br_01") -> dict:
    return {
        "shot_id": shot_id,
        "type": "broll",
        "content": "some broll context",
    }


class TestExecuteKeyframeAgent:
    """Unit tests for _execute_keyframe_agent() with mocked subprocess."""

    def _import_fn(self):
        from src.backend.api.routes.projects import _execute_keyframe_agent
        return _execute_keyframe_agent

    def _mock_open_storyboard(self, shots: list[dict]):
        """Return a mock for builtins.open that reads our storyboard."""
        real_open = open
        storyboard_json = json.dumps(_make_storyboard(shots))

        def _open_side_effect(file, mode="r", *args, **kwargs):
            if "storyboard.json" in str(file):
                return mock.mock_open(read_data=storyboard_json).return_value
            return real_open(file, mode, *args, **kwargs)

        return mock.patch("builtins.open", side_effect=_open_side_effect)

    def test_template_shot_calls_node_subprocess(self):
        """AC-1: Template shots trigger Node.js subprocess with correct args."""
        shots = [_make_template_shot("shot_01", "animated_line_chart", end_seconds=10)]

        with self._mock_open_storyboard(shots):
            with mock.patch("os.makedirs"):
                with mock.patch("os.path.exists", return_value=True):
                    with mock.patch("subprocess.run") as mock_run:
                        mock_run.return_value = mock.Mock(
                            returncode=0, stdout="", stderr=""
                        )
                        with mock.patch("shutil.which", return_value="/usr/local/bin/node"):
                            fn = self._import_fn()
                            db = sqlite3.connect(":memory:")
                            result = fn(db, "test-p8", "Test Title", "Test Description")

        renders = result["renders"]
        assert len(renders) == 1
        assert renders[0]["shot_id"] == "shot_01"
        assert renders[0]["engine"] == "remotion"
        assert renders[0]["degraded"] is False
        assert renders[0]["render_path"].endswith(".mp4")

        # Verify subprocess.run was called with proper Node.js args
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "/usr/local/bin/node"
        shot_id_idx = call_args.index("--shot-id")
        assert call_args[shot_id_idx + 1] == "shot_01"
        template_idx = call_args.index("--template")
        assert call_args[template_idx + 1] == "animated_line_chart"

    def test_broll_shot_skipped(self):
        """AC-3: BRoll shots return render_path=None, no subprocess call."""
        shots = [_make_broll_shot("br_01")]

        with self._mock_open_storyboard(shots):
            with mock.patch("os.makedirs"):
                with mock.patch("subprocess.run") as mock_run:
                    fn = self._import_fn()
                    db = sqlite3.connect(":memory:")
                    result = fn(db, "test-p8", "Test", "Desc")

        mock_run.assert_not_called()
        renders = result["renders"]
        assert len(renders) == 1
        assert renders[0]["shot_id"] == "br_01"
        assert renders[0]["type"] == "broll"
        assert renders[0]["render_path"] is None

    def test_node_unavailable_falls_back_to_pillow(self):
        """AC-2: When Node is not in PATH, fall back to Pillow KeyframeRenderAgent."""
        shots = [_make_template_shot("shot_01", "text_card", end_seconds=5)]

        with self._mock_open_storyboard(shots):
            with mock.patch("os.makedirs"):
                with mock.patch("os.path.exists", return_value=False):
                    with mock.patch("shutil.which", return_value=None):
                        with mock.patch(
                            "src.backend.agents.keyframe_render_agent.KeyframeRenderAgent"
                        ) as mock_agent_class:
                            mock_agent = mock.Mock()
                            mock_agent.render_with_degradation.return_value = {
                                "shot_id": "shot_01",
                                "render_path": "phase_8/shot_01.png",
                                "degraded": True,
                            }
                            mock_agent_class.return_value = mock_agent

                            fn = self._import_fn()
                            db = sqlite3.connect(":memory:")
                            result = fn(db, "test-p8", "Test", "Desc")

        renders = result["renders"]
        assert len(renders) == 1
        assert renders[0]["render_path"].endswith(".png")

    def test_node_render_failure_falls_back_to_pillow(self):
        """AC-4: Node subprocess failure triggers Pillow fallback."""
        shots = [_make_template_shot("shot_01", "data_card", end_seconds=10)]

        with self._mock_open_storyboard(shots):
            with mock.patch("os.makedirs"):
                with mock.patch("os.path.exists", return_value=False):
                    with mock.patch("subprocess.run") as mock_run:
                        mock_run.side_effect = Exception("Node crashed")

                        with mock.patch("shutil.which", return_value="/usr/local/bin/node"):
                            with mock.patch(
                                "src.backend.agents.keyframe_render_agent.KeyframeRenderAgent"
                            ) as mock_agent_class:
                                mock_agent = mock.Mock()
                                mock_agent.render_with_degradation.return_value = {
                                    "shot_id": "shot_01",
                                    "render_path": "phase_8/shot_01.png",
                                    "degraded": True,
                                }
                                mock_agent_class.return_value = mock_agent

                                fn = self._import_fn()
                                db = sqlite3.connect(":memory:")
                                result = fn(db, "test-p8", "Test", "Desc")

        renders = result["renders"]
        assert len(renders) == 1
        assert renders[0]["render_path"].endswith(".png")
