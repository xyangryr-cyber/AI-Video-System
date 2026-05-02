"""[SPEC-D-005] Test that _execute_tts_agent writes timeline.json with measured_duration_sec."""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch


def test_ffprobe_writes_timeline_json(tmp_path, monkeypatch):
    """RED: After TTS audio generation, ffprobe measurement is written to timeline.json."""
    from src.backend.api.routes.projects import _execute_tts_agent

    project_id = "test_proj_001"

    # Change to temp directory so relative paths work
    monkeypatch.chdir(tmp_path)

    # Create data/projects/{project_id}/ structure
    proj_dir = os.path.join("data", "projects", project_id)
    os.makedirs(proj_dir)

    # Write fake polished_script.json
    polished = {
        "segments": [
            {
                "segment_id": "seg_0",
                "polished_text": "test content",
                "content": "test content",
                "word_count": 10,
            }
        ]
    }
    with open(os.path.join(proj_dir, "polished_script.json"), "w") as f:
        json.dump(polished, f)

    # Create audio dir
    os.makedirs(os.path.join(proj_dir, "phase_4"), exist_ok=True)

    # Create a fake audio file that _combine_audio_files can "process"
    fake_audio = os.path.join(proj_dir, "phase_4", "narration_seg_00.mp3")
    with open(fake_audio, "w") as f:
        f.write("fake audio")

    # Mock subprocess.run:
    # - 1st call: _combine_audio_files calls ffmpeg (needs returncode=0)
    # - 2nd call: _write_measured_timeline calls ffprobe (needs stdout="81.5")
    mock_ffmpeg = MagicMock()
    mock_ffmpeg.returncode = 0

    mock_ffprobe = MagicMock()
    mock_ffprobe.stdout = "81.5"

    # Patch at source modules because imports are inside the function body
    with patch(
        "src.backend.services.bytedance_tts_provider.ByteDanceTTSProvider"
    ) as mock_prov_cls, patch(
        "src.backend.agents.tts_agent.TTSAgent"
    ) as mock_agent_cls, patch(
        "subprocess.run", side_effect=[mock_ffmpeg, mock_ffprobe]
    ), patch(
        "shutil.which", return_value="/usr/bin/ffmpeg"
    ):
        # Setup ByteDanceTTSProvider mock
        mock_prov = MagicMock()
        mock_prov_cls.return_value = mock_prov
        mock_prov.synthesize.return_value = {
            "fallback": False,
            "audio_path": fake_audio,
            "duration_seconds": 3.0,
        }

        # Setup TTSAgent mock
        mock_agent = MagicMock()
        mock_agent.build_timeline.return_value = {
            "segments": [
                {
                    "segment_id": "seg_0",
                    "start_sec": 0,
                    "end_sec": 3,
                    "audio_path": fake_audio,
                    "duration_seconds": 3.0,
                }
            ],
            "total_duration_sec": 3.0,
        }
        mock_agent_cls.return_value = mock_agent

        # Execute — the mocked ffmpeg/subprocess won't actually create files,
        # so we need to create narration_master.mp3 manually for the ffprobe step.
        master_path = os.path.join(proj_dir, "phase_4", "narration_master.mp3")
        with open(master_path, "w") as f:
            f.write("fake combined audio")

        _execute_tts_agent(None, project_id, "Test Title", "Test Desc")

        # Verify timeline.json exists and has correct content
        timeline_path = os.path.join(proj_dir, "timeline.json")
        assert os.path.exists(
            timeline_path
        ), f"timeline.json not found at {timeline_path}"

        with open(timeline_path) as f:
            data = json.load(f)

        assert data["project_id"] == project_id
        assert data["phase"] == 4
        assert data["measured_duration_sec"] == 81.5
        assert data["source"] == "ffprobe"


def test_ffprobe_failure_does_not_crash(tmp_path, monkeypatch):
    """If ffprobe fails, _execute_tts_agent should still complete without timeline.json."""
    from src.backend.api.routes.projects import _execute_tts_agent

    project_id = "test_proj_002"
    monkeypatch.chdir(tmp_path)

    proj_dir = os.path.join("data", "projects", project_id)
    os.makedirs(proj_dir)

    polished = {
        "segments": [
            {
                "segment_id": "seg_0",
                "polished_text": "test",
                "content": "test",
                "word_count": 3,
            }
        ]
    }
    with open(os.path.join(proj_dir, "polished_script.json"), "w") as f:
        json.dump(polished, f)

    os.makedirs(os.path.join(proj_dir, "phase_4"), exist_ok=True)
    fake_audio = os.path.join(proj_dir, "phase_4", "narration_seg_00.mp3")
    with open(fake_audio, "w") as f:
        f.write("fake audio")

    # Mock subprocess.run: ffmpeg succeeds, ffprobe raises
    mock_ffmpeg = MagicMock()
    mock_ffmpeg.returncode = 0

    with patch(
        "src.backend.services.bytedance_tts_provider.ByteDanceTTSProvider"
    ) as mock_prov_cls, patch(
        "src.backend.agents.tts_agent.TTSAgent"
    ) as mock_agent_cls, patch(
        "subprocess.run",
        side_effect=[mock_ffmpeg, RuntimeError("ffprobe not available")],
    ), patch(
        "shutil.which", return_value="/usr/bin/ffmpeg"
    ):
        mock_prov = MagicMock()
        mock_prov_cls.return_value = mock_prov
        mock_prov.synthesize.return_value = {
            "fallback": False,
            "audio_path": fake_audio,
            "duration_seconds": 2.0,
        }

        mock_agent = MagicMock()
        mock_agent.build_timeline.return_value = {
            "segments": [
                {
                    "segment_id": "seg_0",
                    "start_sec": 0,
                    "end_sec": 2,
                    "audio_path": fake_audio,
                    "duration_seconds": 2.0,
                }
            ],
            "total_duration_sec": 2.0,
        }
        mock_agent_cls.return_value = mock_agent

        # Should not crash
        result = _execute_tts_agent(None, project_id, "Test", "Desc")
        assert result is not None

        # timeline.json should NOT exist
        timeline_path = os.path.join(proj_dir, "timeline.json")
        assert not os.path.exists(timeline_path)
