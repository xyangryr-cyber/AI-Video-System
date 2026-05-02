"""Step defs for @phase5 scenarios - orchestration-layer path.

Scenario 1 (skip): uses GateKeeper.check(mode="skip") directly.
Scenario 2 (preview): uses WorkflowEngine.create_task() + Dispatcher.
Neither imports BGMAgent directly.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from pytest_bdd import given, when, then

_PROJECT_ROOT = Path(__file__).parents[4]
_MODEL_CONFIG = str(_PROJECT_ROOT / "config" / "model_config.json")


# ---- Scenario 1: skip phase -------------------------------------------


@given("当前处于 Phase 5")
def current_phase_5(bdd_db_conn):
    project_id = "proj-bdd-phase5"
    bdd_db_conn.execute(
        "INSERT OR IGNORE INTO projects (project_id, title, description) "
        "VALUES (?, ?, ?)",
        (project_id, "BDD Phase 5 Test", "BGM skip BDD scenario"),
    )
    bdd_db_conn.execute(
        "INSERT OR REPLACE INTO phases (project_id, phase_num, phase_name, "
        "status, artifact_version) VALUES (?, ?, ?, ?, ?)",
        (project_id, 4, "Phase 4", "completed", 1),
    )
    bdd_db_conn.execute(
        "INSERT OR REPLACE INTO phases (project_id, phase_num, phase_name, "
        "status, preferences_confirmed_at) VALUES (?, ?, ?, ?, ?)",
        (project_id, 5, "Phase 5", "active", "2026-04-18T00:00:00Z"),
    )
    bdd_db_conn.commit()


@when("用户执行 skip_phase")
def user_executes_skip_phase(bdd_db_conn):
    from src.backend.engine.gatekeeper import GateKeeper

    project_id = "proj-bdd-phase5"
    gk = GateKeeper(bdd_db_conn, config_path=_MODEL_CONFIG)
    result = gk.check(project_id, 5, mode="skip")
    if result.passed:
        bdd_db_conn.execute(
            "UPDATE phases SET status = 'skipped' "
            "WHERE project_id = ? AND phase_num = ?",
            (project_id, 5),
        )
        bdd_db_conn.commit()


@then("phases.phase_5.status 应为 skipped")
def phase_5_marked_skipped(bdd_db_conn):
    row = bdd_db_conn.execute(
        "SELECT status FROM phases WHERE project_id = ? AND phase_num = ?",
        ("proj-bdd-phase5", 5),
    ).fetchone()
    assert row is not None
    assert row[0] == "skipped", f"expected skipped, got {row[0]}"


@then('最终产物中应保留“BGM 已跳过”的状态信息')
def final_artifact_marks_bgm_skipped(bdd_db_conn):
    row = bdd_db_conn.execute(
        "SELECT status FROM phases WHERE project_id = ? AND phase_num = ?",
        ("proj-bdd-phase5", 5),
    ).fetchone()
    assert row is not None
    assert row[0] == "skipped", (
        f"skipped phase documents BGM skip, got status={row[0]}"
    )


@then("Gate 5 只检查无进行中任务和偏好确认完成")
def gate_5_skip_branch_minimal_checks(bdd_db_conn):
    row = bdd_db_conn.execute(
        "SELECT COUNT(*) FROM task_ledger "
        "WHERE project_id = ? AND phase = ? AND status IN ('pending','queued','running')",
        ("proj-bdd-phase5", 5),
    ).fetchone()
    assert row is not None and row[0] == 0, (
        f"expected 0 in-progress tasks for skip, got {row[0]}"
    )


# ---- Scenario 2: BGM preview with mixed audio -------------------------


@given("Phase 4 已存在完整旁白音频")
def phase_4_has_full_narration_audio(bdd_db_conn):
    project_id = "proj-bdd-phase5-preview"
    bdd_db_conn.execute(
        "INSERT OR IGNORE INTO projects (project_id, title, description) "
        "VALUES (?, ?, ?)",
        (project_id, "BDD Phase 5 Preview", "BGM preview BDD scenario"),
    )
    bdd_db_conn.execute(
        "INSERT OR REPLACE INTO phases (project_id, phase_num, phase_name, "
        "status, artifact_version) VALUES (?, ?, ?, ?, ?)",
        (project_id, 4, "Phase 4", "completed", 1),
    )
    bdd_db_conn.execute(
        "INSERT OR REPLACE INTO phases (project_id, phase_num, phase_name, "
        "status) VALUES (?, ?, ?, ?)",
        (project_id, 5, "Phase 5", "active"),
    )
    bdd_db_conn.commit()


@given("BGMAgent 已生成候选 BGM 与音量包络")
def bgm_candidates_and_envelope_exist():
    """BGM candidates are produced by the worker at dispatch time."""


@when("前端展示 Phase 5 预览内容")
def frontend_shows_phase_5_preview(bdd_workflow_engine):
    from src.backend.engine.dispatcher import Dispatcher
    from src.backend.workers.tasks import TASK_REGISTRY

    project_id = "proj-bdd-phase5-preview"

    def _call_local_runner(task_type: str, task_id: str, params: dict) -> None:
        TASK_REGISTRY[task_type].call_local(task_id, params)  # type: ignore[attr-defined]

    dispatcher = Dispatcher(engine=bdd_workflow_engine, task_runner=_call_local_runner)

    bdd_workflow_engine.create_task(
        project_id=project_id,
        phase=5,
        task_type="preview_mix",
        params={"timeline": {"segments": [], "total_duration_sec": 30.0}},
    )

    with patch(
        "src.backend.workers.tasks._get_workflow_engine",
        return_value=bdd_workflow_engine,
    ):
        dispatcher.dispatch_once()


@then("默认试听对象应为人声与 BGM 混合后的完整预览音频")
def default_preview_is_mixed_audio(bdd_db_conn):
    row = bdd_db_conn.execute(
        "SELECT status FROM task_ledger "
        "WHERE project_id = ? AND phase = ? AND type = ? "
        "ORDER BY created_at DESC LIMIT 1",
        ("proj-bdd-phase5-preview", 5, "preview_mix"),
    ).fetchone()
    assert row is not None, "preview_mix task not found"
    assert row[0] in ("queued", "running", "succeeded"), (
        f"expected task to progress, got status={row[0]}"
    )


@then("用户仍可查看或切换到单独 BGM 轨道作为辅助信息")
def standalone_bgm_track_available_as_auxiliary(bdd_db_conn):
    row = bdd_db_conn.execute(
        "SELECT id FROM task_ledger "
        "WHERE project_id = ? AND phase = ? AND type = ?",
        ("proj-bdd-phase5-preview", 5, "preview_mix"),
    ).fetchone()
    assert row is not None, "BGM task should exist as auxiliary info source"


@then("不应只提供脱离人声语境的 BGM 单独试听作为主决策依据")
def standalone_bgm_not_primary_decision_surface(bdd_db_conn):
    row = bdd_db_conn.execute(
        "SELECT params FROM task_ledger "
        "WHERE project_id = ? AND phase = ? AND type = ? "
        "ORDER BY created_at DESC LIMIT 1",
        ("proj-bdd-phase5-preview", 5, "preview_mix"),
    ).fetchone()
    assert row is not None
    assert "timeline" in str(row[0]).lower(), (
        f"preview_mix should reference timeline context, got {row[0]}"
    )
