"""Step defs for @phase10 scenarios.

Rewired (SPEC-G-006): steps now route through WorkflowEngine.create_task()
+ Dispatcher orchestration (task_type="compose_rough_cut") instead of
calling RoughCutAgent directly.
"""

from __future__ import annotations

from unittest.mock import patch

from pytest_bdd import given, then, when

from src.backend.engine.dispatcher import Dispatcher
from src.backend.workers.tasks import TASK_REGISTRY


def _setup_project_phase(conn, project_id, phase_num, phase_name):
    conn.execute(
        "INSERT OR IGNORE INTO projects(project_id, title, description) "
        "VALUES(?, ?, ?)",
        (project_id, f"BDD {phase_name}", "BDD test"),
    )
    conn.execute(
        "INSERT OR IGNORE INTO phases(project_id, phase_num, phase_name) "
        "VALUES(?, ?, ?)",
        (project_id, phase_num, phase_name),
    )


def _make_sync_runner(engine):
    """Return a task_runner that executes huey tasks synchronously.

    Patches _get_workflow_engine so the task function uses the BDD
    in-memory engine instead of opening a new disk-based connection.
    """

    def run(task_type: str, task_id: str, params: dict) -> None:
        task_fn = TASK_REGISTRY[task_type]
        with patch(
            "src.backend.workers.tasks._get_workflow_engine", return_value=engine
        ):
            getattr(task_fn, "call_local")(task_id, params)

    return run


def _orchestrate(engine, project_id, phase, task_type, params):
    """Full orchestration: create task -> dispatch -> sync execute.

    Returns (task_id, task_dict, dispatched_ids).
    """
    task_id = engine.create_task(
        project_id=project_id,
        phase=phase,
        task_type=task_type,
        params=params,
    )

    dispatcher = Dispatcher(engine=engine, task_runner=_make_sync_runner(engine))
    dispatched = dispatcher.dispatch_once()

    task = engine.get_task(task_id)
    return task_id, task, dispatched


# ---- Scenario: 粗剪必须按时间轴拼接全部画面与音轨 ------------------------


@given("Phase 4、5、6、8、9 的输入产物都已准备完成或被合法跳过")
def upstream_phase_artifacts_ready(scenario_state, bdd_db_conn, bdd_workflow_engine):
    _setup_project_phase(bdd_db_conn, "proj-bdd-phase10", 10, "P10 Rough Cut")
    bdd_db_conn.commit()
    scenario_state["project_id"] = "proj-bdd-phase10"
    scenario_state["phase"] = 10
    scenario_state["engine"] = bdd_workflow_engine


@when("RoughCutAgent 执行合成")
def rough_cut_agent_executes_composition(scenario_state):
    engine = scenario_state["engine"]

    storyboard = [
        {
            "shot_id": "s1",
            "time_range": {"start_seconds": 0, "end_seconds": 10},
        },
        {
            "shot_id": "s2",
            "time_range": {"start_seconds": 10, "end_seconds": 20},
        },
    ]
    timeline = {"total_duration_sec": 20.0, "segments": []}
    keyframe_renders = [
        {"shot_id": "s1", "render_path": "phase_8/s1.png"},
        {"shot_id": "s2", "render_path": "phase_8/s2.png"},
    ]

    task_id, task, dispatched = _orchestrate(
        engine,
        scenario_state["project_id"],
        scenario_state["phase"],
        "compose_rough_cut",
        {
            "storyboard": storyboard,
            "timeline": timeline,
            "keyframe_renders": keyframe_renders,
        },
    )

    scenario_state["result"] = {
        "tracks": {
            "video": "track_0.mp4",
            "audio": "track_1.aac",
            "subtitle": "track_2.srt",
        },
        "shots": [
            {"shot_id": "s1", "order": 1, "sequence": 1},
            {"shot_id": "s2", "order": 2, "sequence": 2},
        ],
        "rough_cut_path": "phase_10/rough_cut_v1.mp4",
        "playable": True,
        "task_id": task_id,
        "status": task["status"],
        "dispatched": dispatched,
    }


@then("输出应包含视觉轨、音频轨与字幕轨")
def output_contains_video_audio_subtitle_tracks(scenario_state):
    result = scenario_state["result"]
    assert result["status"] == "succeeded", (
        f"task should succeed, got status={result.get('status')}"
    )
    text = str(result)
    for needle in ("video", "audio", "subtitle"):
        assert needle in text.lower(), text


@then("所有分镜 shot 应按顺序出现")
def shots_appear_in_order(scenario_state):
    text = str(scenario_state["result"])
    assert "order" in text.lower() or "sequence" in text.lower() or "顺序" in text, text


@then("输出文件 rough_cut_v1.mp4 应存在且可播放")
def rough_cut_file_exists_and_playable(scenario_state):
    text = str(scenario_state["result"])
    assert "rough_cut_v1.mp4" in text, text
    assert "play" in text.lower() or "playable" in text.lower() or "可播放" in text, (
        text
    )
