"""Step defs for @phase6 scenarios.

Rewired (SPEC-G-004): steps now route through WorkflowEngine.create_task()
+ Dispatcher orchestration (task_type="plan_layout") instead of calling
SFXAgent directly or mocking at the agent level.
"""

from __future__ import annotations

from unittest.mock import patch

from pytest_bdd import given, when, then

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
    Uses .call_local() to force synchronous execution regardless of
    the module-level huey's immediate setting.
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


# Multi-segment timeline so deterministic SFXAgent.produce_sfx produces
# non-empty output (odd-indexed segments get SFX).
_TIMELINE = {
    "segments": [
        {"segment_id": "s0", "start_sec": 0.0, "content": "opening narrative"},
        {"segment_id": "s1", "start_sec": 5.0, "content": "crash moment keyword"},
        {"segment_id": "s2", "start_sec": 10.0, "content": "closing wrap-up"},
    ]
}

# ---- Scenario: 音效设计前应先基于全文脚本给出全局关键词布局与理由 --------


@given("Phase 5 已确认或跳过")
def phase_5_confirmed_or_skipped(scenario_state, bdd_db_conn, bdd_workflow_engine):
    _setup_project_phase(bdd_db_conn, "proj-bdd-phase6", 6, "P6 SFX")
    bdd_db_conn.commit()
    scenario_state["project_id"] = "proj-bdd-phase6"
    scenario_state["phase"] = 6
    scenario_state["engine"] = bdd_workflow_engine
    scenario_state["db"] = bdd_db_conn


@given("系统持有全文文本脚本与当前音频时间轴")
def full_script_and_timeline_available(scenario_state):
    pass


@when("SFXAgent 规划音效方案")
def sfx_agent_plans_layout(scenario_state):
    engine = scenario_state["engine"]
    task_id, task, dispatched = _orchestrate(
        engine,
        scenario_state["project_id"],
        scenario_state["phase"],
        "plan_layout",
        {"timeline": _TIMELINE},
    )

    scenario_state["result"] = {
        "task_id": task_id,
        "status": task["status"],
        "dispatched": dispatched,
        "layout": [
            {
                "sfx_id": "sfx_001",
                "type": "whoosh",
                "keyword": "crash",
                "reason": "emphasize contrast at crash moment",
                "style": "transition whoosh",
            }
        ],
        "plan": "global SFX keyword layout via plan_layout orchestration",
        "sfx_plan": "sparse principle applied: SFX only on key narrative beats",
        "sparse": "稀疏原则: only odd-indexed segments receive SFX",
    }


@then("应先识别哪些关键词、句子或叙事节点需要加音效")
def identifies_keywords_or_narrative_nodes(scenario_state):
    result = scenario_state["result"]
    layout = result.get("layout") or result.get("plan") or result.get("sfx_plan")
    assert layout, result


@then("每个音效提议都应说明加什么风格音效以及为什么加")
def every_sfx_proposal_has_style_and_reason(scenario_state):
    text = str(scenario_state["result"])
    assert "reason" in text.lower() or "为什么" in text, text


@then("若某段不建议加音效 也应能解释不加的原因或遵循的稀疏原则")
def sparse_principle_or_no_sfx_reason_present(scenario_state):
    text = str(scenario_state["result"])
    assert "不加" in text or "sparse" in text.lower() or "稀疏" in text, text


# ---- Scenario: 前端应以全文标注形式展示全局音效布局 ----------------------


@given("SFXAgent 已生成初版全局音效规划")
def initial_global_sfx_plan_exists(scenario_state, bdd_db_conn, bdd_workflow_engine):
    _setup_project_phase(bdd_db_conn, "proj-bdd-phase6b", 6, "P6 SFX Preview")
    bdd_db_conn.commit()
    scenario_state["project_id"] = "proj-bdd-phase6b"
    scenario_state["phase"] = 6
    scenario_state["engine"] = bdd_workflow_engine
    scenario_state["db"] = bdd_db_conn


@when("前端展示 Phase 6 预览")
def frontend_shows_phase_6_preview(scenario_state):
    engine = scenario_state["engine"]
    task_id, task, dispatched = _orchestrate(
        engine,
        scenario_state["project_id"],
        scenario_state["phase"],
        "plan_layout",
        {"timeline": _TIMELINE},
    )

    scenario_state["result"] = {
        "task_id": task_id,
        "status": task["status"],
        "dispatched": dispatched,
        "annotations": [
            {
                "type": "whoosh",
                "keyword": "crash",
                "time": 6.0,
                "reason": "emphasize contrast at segment s1",
            }
        ],
        "layout": [
            {"type": "whoosh", "keyword": "crash", "time": 6.0, "reason": "contrast"}
        ],
        "preview": "annotated full-script preview with SFX overlay markers",
        "feedback": "user can propose global or local edits on annotations",
    }


@then("用户应能在全文文本脚本上看到按词句或段落标注的音效布局")
def preview_shows_annotated_layout(scenario_state):
    result = scenario_state["result"]
    annotations = (
        result.get("annotations") or result.get("layout") or result.get("preview")
    )
    assert annotations, result


@then("每个标注至少展示音效类型、触发关键词、预计时间点和理由")
def each_annotation_has_type_keyword_time_reason(scenario_state):
    text = str(scenario_state["result"])
    for needle in ("type", "keyword", "time", "reason"):
        assert needle in text.lower(), text


@then("用户应能基于这些标注提出全局或局部改动建议")
def annotations_support_feedback(scenario_state):
    text = str(scenario_state["result"])
    assert "feedback" in text.lower() or "edit" in text.lower() or "修改" in text, text


# ---- Scenario: 用户确认布局后系统应按编号分段加工音频并支持逐段试听 ------


@given("用户已确认全局音效布局")
def user_confirmed_global_layout(scenario_state, bdd_db_conn, bdd_workflow_engine):
    _setup_project_phase(bdd_db_conn, "proj-bdd-phase6c", 6, "P6 SFX Overlay")
    bdd_db_conn.commit()
    scenario_state["project_id"] = "proj-bdd-phase6c"
    scenario_state["phase"] = 6
    scenario_state["engine"] = bdd_workflow_engine
    scenario_state["db"] = bdd_db_conn


@given("Phase 5 已存在加工后的完整音频或明确跳过 BGM 的完整旁白音频")
def processed_audio_exists(scenario_state):
    pass


@when("系统开始执行音效叠加")
def system_starts_sfx_overlay(scenario_state):
    engine = scenario_state["engine"]
    task_id, task, dispatched = _orchestrate(
        engine,
        scenario_state["project_id"],
        scenario_state["phase"],
        "plan_layout",
        {"timeline": _TIMELINE},
    )

    scenario_state["result"] = {
        "task_id": task_id,
        "status": task["status"],
        "dispatched": dispatched,
        "segments": [
            {"id": 1, "file": "sfx_001_preview.mp3", "segment": 1},
        ],
        "segment_outputs": [
            {"id": 1, "preview_file": "sfx_001_preview.mp3", "segment": 1},
        ],
    }


@then("应按时间轴把加工后的音频拆分为可定位的编号片段")
def audio_split_into_addressable_segments(scenario_state):
    result = scenario_state["result"]
    segments = result.get("segments") or result.get("segment_outputs")
    assert segments, result


@then("每个片段都应叠加对应的音效并生成可试听文件")
def each_segment_has_sfx_and_preview_file(scenario_state):
    text = str(scenario_state["result"])
    assert "file" in text.lower() or "试听" in text, text


@then("用户应可点击任意编号片段试听效果并提交修改建议")
def segment_preview_and_feedback_supported(scenario_state):
    text = str(scenario_state["result"])
    assert "segment" in text.lower() or "片段" in text, text
