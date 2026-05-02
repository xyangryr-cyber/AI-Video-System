"""[SPEC-D-005] Test that downstream agents propagate measured_duration_sec from timeline.json."""

from __future__ import annotations

import json
import os


# -- StoryboardAgent tests ---------------------------------------------------


def test_storyboard_uses_measured_duration_even_split():
    """Given measured_duration_sec=81.5, storyboard shot time_ranges should sum ~81.5."""
    from src.backend.agents.storyboard_agent import StoryboardAgent

    timeline = {
        "segments": [
            {
                "segment_id": "seg_0",
                "start_sec": 0,
                "end_sec": 60,
                "emotion_tone": "neutral",
                "content": "test content A",
            },
            {
                "segment_id": "seg_1",
                "start_sec": 60,
                "end_sec": 120,
                "emotion_tone": "neutral",
                "content": "test content B",
            },
            {
                "segment_id": "seg_2",
                "start_sec": 120,
                "end_sec": 180,
                "emotion_tone": "neutral",
                "content": "test content C",
            },
        ]
    }
    script = [{} for _ in range(3)]

    shots = StoryboardAgent.produce_storyboard(
        timeline=timeline, script=script, measured_duration_sec=81.5
    )

    total = sum(
        s["time_range"]["end_seconds"] - s["time_range"]["start_seconds"]
        for s in shots
    )
    assert abs(total - 81.5) < 0.5, f"Expected time_range sum ~81.5, got {total}"


def test_storyboard_no_measured_duration_falls_back_to_timeline():
    """Without measured_duration_sec, storyboard should use original timeline start/end."""
    from src.backend.agents.storyboard_agent import StoryboardAgent

    timeline = {
        "segments": [
            {
                "segment_id": "seg_0",
                "start_sec": 0,
                "end_sec": 60,
                "emotion_tone": "neutral",
                "content": "test",
            },
            {
                "segment_id": "seg_1",
                "start_sec": 60,
                "end_sec": 120,
                "emotion_tone": "neutral",
                "content": "test",
            },
        ]
    }
    script = [{}, {}]

    shots = StoryboardAgent.produce_storyboard(timeline=timeline, script=script)

    total = sum(
        s["time_range"]["end_seconds"] - s["time_range"]["start_seconds"]
        for s in shots
    )
    assert (
        abs(total - 120.0) < 0.5
    ), f"Expected fallback to timeline total (120), got {total}"


# -- RoughCutAgent tests -----------------------------------------------------


def test_rough_cut_uses_measured_duration():
    """Given measured_duration_sec=81.5, RoughCutAgent compose uses it as duration_seconds."""
    from src.backend.agents.rough_cut_agent import RoughCutAgent

    storyboard = [
        {
            "shot_id": "shot_000",
            "time_range": {"start_seconds": 0, "end_seconds": 10},
            "type": "template",
        },
        {
            "shot_id": "shot_001",
            "time_range": {"start_seconds": 10, "end_seconds": 20},
            "type": "broll",
        },
    ]

    result = RoughCutAgent.compose(
        project_id="proj_test",
        storyboard=storyboard,
        timeline={},
        keyframe_renders=[],
        measured_duration_sec=81.5,
    )

    assert result["duration_seconds"] == 81.5, (
        f"Expected duration_seconds=81.5, got {result['duration_seconds']}"
    )


def test_rough_cut_no_measured_duration_falls_back_to_timeline_sum():
    """Without measured_duration_sec, compose should fall back to storyboard time_range sum."""
    from src.backend.agents.rough_cut_agent import RoughCutAgent

    storyboard = [
        {
            "shot_id": "shot_000",
            "time_range": {"start_seconds": 0, "end_seconds": 30},
            "type": "template",
        },
        {
            "shot_id": "shot_001",
            "time_range": {"start_seconds": 30, "end_seconds": 60},
            "type": "broll",
        },
    ]

    result = RoughCutAgent.compose(
        project_id="proj_test", storyboard=storyboard, timeline={}, keyframe_renders=[]
    )

    assert (
        result["duration_seconds"] == 60.0
    ), f"Expected fallback to timeline sum (60), got {result['duration_seconds']}"


# -- _execute_* functions read timeline.json + pass measured_duration ---------


def test_execute_storyboard_reads_timeline_json(tmp_path, monkeypatch):
    """_execute_storyboard_agent reads timeline.json and passes measured_duration_sec."""
    from src.backend.api.routes.projects import _execute_storyboard_agent

    project_id = "test_proj_sb"
    monkeypatch.chdir(tmp_path)

    proj_dir = os.path.join("data", "projects", project_id)
    os.makedirs(proj_dir)

    # Write timeline.json with measured_duration_sec
    timeline_json = {
        "project_id": project_id,
        "phase": 4,
        "measured_duration_sec": 81.5,
        "source": "ffprobe",
    }
    with open(os.path.join(proj_dir, "timeline.json"), "w") as f:
        json.dump(timeline_json, f)

    # Write narration.json (timeline from P4)
    narr = {
        "segments": [
            {
                "segment_id": "seg_0",
                "start_sec": 0,
                "end_sec": 200,
                "emotion_tone": "neutral",
                "content": "test A",
            },
            {
                "segment_id": "seg_1",
                "start_sec": 200,
                "end_sec": 400,
                "emotion_tone": "neutral",
                "content": "test B",
            },
        ],
        "total_duration_sec": 600,
    }
    with open(os.path.join(proj_dir, "narration.json"), "w") as f:
        json.dump(narr, f)

    # Write script_v1.json
    script_v1 = [{"segment_id": "seg_0"}, {"segment_id": "seg_1"}]
    with open(os.path.join(proj_dir, "script_v1.json"), "w") as f:
        json.dump(script_v1, f)

    result = _execute_storyboard_agent(None, project_id, "Test", "Desc")

    # Verify shots were produced
    assert "shots" in result
    shots = result["shots"]
    total = sum(
        s["time_range"]["end_seconds"] - s["time_range"]["start_seconds"]
        for s in shots
    )
    assert abs(total - 81.5) < 0.5, f"Expected time_range sum ~81.5, got {total}"


def test_execute_rough_cut_reads_timeline_json(tmp_path, monkeypatch):
    """_execute_rough_cut_agent reads timeline.json and uses measured_duration_sec."""
    from src.backend.api.routes.projects import _execute_rough_cut_agent

    project_id = "test_proj_rc"
    monkeypatch.chdir(tmp_path)

    proj_dir = os.path.join("data", "projects", project_id)
    os.makedirs(proj_dir)

    # Write timeline.json
    timeline_json = {
        "project_id": project_id,
        "phase": 4,
        "measured_duration_sec": 81.5,
        "source": "ffprobe",
    }
    with open(os.path.join(proj_dir, "timeline.json"), "w") as f:
        json.dump(timeline_json, f)

    # Write storyboard.json
    sb = {
        "shots": [
            {
                "shot_id": "shot_000",
                "time_range": {"start_seconds": 0, "end_seconds": 30},
                "type": "template",
                "template_type": "text_card",
            },
            {
                "shot_id": "shot_001",
                "time_range": {"start_seconds": 30, "end_seconds": 60},
                "type": "broll",
                "template_type": None,
            },
        ]
    }
    with open(os.path.join(proj_dir, "storyboard.json"), "w") as f:
        json.dump(sb, f)

    # narration.json needed for the function but may not exist
    # _execute_rough_cut_agent reads it but can handle missing file

    result = _execute_rough_cut_agent(None, project_id, "Test", "Desc")

    assert (
        result["duration_seconds"] == 81.5
    ), f"Expected duration_seconds=81.5, got {result['duration_seconds']}"
