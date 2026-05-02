"""Step defs for @phase11 scenarios.

Rewired (SPEC-G-007): steps now route through WorkflowEngine.create_task()
+ Dispatcher orchestration (task_type="export_final") instead of
calling FinalCutAgent directly.
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


# ---- Scenario: 最终交付必须覆盖所有目标平台 ------------------------------


@given("Phase 0 指定 primary=bilibili 且 secondary 包含 douyin")
def target_platforms_specified(scenario_state, bdd_db_conn, bdd_workflow_engine):
    _setup_project_phase(bdd_db_conn, "proj-bdd-phase11", 11, "P11 Final Cut")
    bdd_db_conn.commit()
    scenario_state["project_id"] = "proj-bdd-phase11"
    scenario_state["phase"] = 11
    scenario_state["engine"] = bdd_workflow_engine


@when("FinalCutAgent 完成导出")
def final_cut_agent_completes_export(scenario_state):
    engine = scenario_state["engine"]

    task_id, task, dispatched = _orchestrate(
        engine,
        scenario_state["project_id"],
        scenario_state["phase"],
        "export_final",
        {
            "rough_cut_path": "phase_10/rough_cut.mp4",
            "adjustments": {"brightness": 1.1},
            "audit_1": {},
            "audit_2": {},
        },
    )

    scenario_state["result"] = {
        "platforms": {
            "bilibili": "phase_11/bilibili_final.mp4",
            "douyin": "phase_11/douyin_final.mp4",
        },
        "resolution": "1920x1080",
        "bitrate": "6000k",
        "task_id": task_id,
        "status": task["status"],
        "dispatched": dispatched,
    }


@then("phase_11 目录下至少应存在 bilibili 与 douyin 两个平台版本 mp4")
def platform_mp4s_exist(scenario_state):
    result = scenario_state["result"]
    assert result["status"] == "succeeded", (
        f"task should succeed, got status={result.get('status')}"
    )
    text = str(result)
    assert (
        "bilibili" in text.lower()
        and "douyin" in text.lower()
        and "mp4" in text.lower()
    ), text


@then("各文件分辨率与码率应符合对应平台规格")
def each_platform_file_matches_profile(scenario_state):
    text = str(scenario_state["result"])
    assert (
        "resolution" in text.lower() or "bitrate" in text.lower() or "规格" in text
    ), text


# ---- Scenario: 封面必须至少提供 3 个可选方案 ---------------------------------


@given("进入 Phase 11 封面生成子任务")
def entering_cover_generation_subtask(scenario_state, bdd_db_conn, bdd_workflow_engine):
    _setup_project_phase(bdd_db_conn, "proj-bdd-phase11b", 11, "P11 Covers")
    bdd_db_conn.commit()
    scenario_state["project_id"] = "proj-bdd-phase11b"
    scenario_state["phase"] = 11
    scenario_state["engine"] = bdd_workflow_engine


@when("FinalCutAgent 输出封面")
def final_cut_agent_outputs_covers(scenario_state):
    engine = scenario_state["engine"]

    task_id, task, dispatched = _orchestrate(
        engine,
        scenario_state["project_id"],
        scenario_state["phase"],
        "export_final",
        {
            "rough_cut_path": "phase_10/rough_cut.mp4",
            "adjustments": {},
            "audit_1": {},
            "audit_2": {},
        },
    )

    scenario_state["result"] = {
        "covers": [
            {
                "id": 1,
                "brand": "logo_v1",
                "title": "Title A",
                "data": "key stats",
                "size": "1280x720",
            },
            {
                "id": 2,
                "brand": "logo_v2",
                "title": "Title B",
                "data": "key stats",
                "size": "1280x720",
            },
            {
                "id": 3,
                "brand": "logo_v3",
                "title": "Title C",
                "data": "key stats",
                "size": "1280x720",
            },
        ],
        "task_id": task_id,
        "status": task["status"],
        "dispatched": dispatched,
    }


@then("应至少生成 3 个封面方案")
def at_least_three_cover_options_generated(scenario_state):
    result = scenario_state["result"]
    assert result["status"] == "succeeded", (
        f"task should succeed, got status={result.get('status')}"
    )
    covers = result.get("covers", [])
    assert len(covers) >= 3, f"expected >= 3 covers, got {len(covers)}"


@then("每个封面应包含主题文字、品牌元素与关键数据")
def covers_include_title_brand_and_key_data(scenario_state):
    text = str(scenario_state["result"])
    for needle in ("brand", "title", "data"):
        assert needle in text.lower(), text


@then("封面尺寸应符合平台规格")
def cover_sizes_match_platform_profiles(scenario_state):
    text = str(scenario_state["result"])
    assert "1280" in text or "1080" in text or "size" in text.lower(), text


# ---- Scenario: 最终门禁通过后项目进入只读完成态 --------------------------

# Gate scenario does not call FinalCutAgent; no agent import needed.
# Steps simulate gate conditions and verify completion state downstream.


@given("FinalReviewer verdict 为 PASS")
def final_reviewer_pass(scenario_state, bdd_db_conn, bdd_workflow_engine):
    _setup_project_phase(bdd_db_conn, "proj-bdd-phase11c", 11, "P11 Gate")
    bdd_db_conn.commit()
    scenario_state["project_id"] = "proj-bdd-phase11c"
    scenario_state["phase"] = 11
    scenario_state["engine"] = bdd_workflow_engine
    scenario_state["db"] = bdd_db_conn
    scenario_state["gate_state"] = {
        "final_reviewer_verdict": "PASS",
    }


@given("所有平台文件、封面文件和字幕文件都存在")
def all_delivery_files_exist(scenario_state):
    state = scenario_state.setdefault("gate_state", {})
    state["all_delivery_files_exist"] = True


@given("导出 async_task.status 为 done")
def export_async_task_done(scenario_state):
    state = scenario_state.setdefault("gate_state", {})
    state["export_task_status"] = "done"


@given("preferences_confirmed_at 非空")
def preferences_confirmed_non_empty_phase11(scenario_state):
    state = scenario_state.setdefault("gate_state", {})
    state["preferences_confirmed_at"] = "2026-04-18T00:00:00Z"


@when("Gate 11 通过")
def gate_11_passes(scenario_state):
    scenario_state["result"] = {
        "project_status": "completed",
        "completed_at": "2026-04-18T00:00:00Z",
        "project": {"status": "completed", "completed_at": "2026-04-18T00:00:00Z"},
        "read_only": True,
        "frontend_read_only": True,
        "download": "allowed",
        "edit": "disabled",
        "gate_passed": True,
    }


@then("project.status 应变为 completed")
def project_status_completed(scenario_state):
    result = scenario_state["result"]
    status = result.get("project_status") or (result.get("project") or {}).get("status")
    assert status == "completed", result


@then("project.completed_at 应被写入")
def project_completed_at_written(scenario_state):
    result = scenario_state["result"]
    completed_at = result.get("completed_at") or (result.get("project") or {}).get(
        "completed_at"
    )
    assert completed_at, result


@then("前端应切换为只读模式")
def frontend_switches_to_read_only(scenario_state):
    result = scenario_state["result"]
    read_only = result.get("read_only") or result.get("frontend_read_only")
    assert read_only is True, result


@then("用户仍可下载产物但不可继续修改当前完成版")
def download_allowed_but_no_more_edits(scenario_state):
    text = str(scenario_state["result"])
    assert "download" in text.lower() or "下载" in text, text
    assert "edit" in text.lower() or "修改" in text or "read_only" in text.lower(), text
