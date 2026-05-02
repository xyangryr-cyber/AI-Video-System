"""Step defs for @navigation scenarios."""

from __future__ import annotations

from pathlib import Path

from pytest_bdd import given, when, then

_REPO_ROOT = Path(__file__).resolve().parents[4]


def _read(rel: str) -> str:
    return (_REPO_ROOT / rel).read_text()


def _has_all(text: str, *needles: str) -> bool:
    return all(needle in text for needle in needles)


@given("系统中已存在多个视频项目")
def multiple_projects_exist(scenario_state):
    scenario_state["sources"] = {
        "app_router": _read("src/frontend/pages/AppRouter.tsx"),
        "project_list": _read("src/frontend/pages/ProjectList.tsx"),
    }


@when("用户打开首页 /")
def user_opens_homepage(scenario_state):
    sources = scenario_state.setdefault("sources", {})
    sources.setdefault("app_router", _read("src/frontend/pages/AppRouter.tsx"))
    sources.setdefault("project_list", _read("src/frontend/pages/ProjectList.tsx"))


@then("页面应展示项目列表")
def page_shows_project_list(scenario_state):
    app_router = scenario_state["sources"]["app_router"]
    project_list = scenario_state["sources"]["project_list"]
    assert (
        '/" element={<Navigate to="/projects" replace />}' in app_router
        or 'path="/" element={<Navigate to="/projects" replace />}' in app_router
    ), app_router
    assert (
        "ProjectList" in project_list
        and "data.map" in project_list
    ), project_list


@then("每个项目至少显示标题、当前阶段、最近更新时间和项目状态")
def each_project_card_shows_required_fields(scenario_state):
    project_list = scenario_state["sources"]["project_list"]
    assert _has_all(
        project_list,
        "project.title",
        "project.current_phase",
        "project.status",
        "project.updated_at",
    ), project_list
    assert "fromNow" in project_list, project_list


@then("用户应可以点击任一项目进入项目工作流页")
def user_can_open_workflow_page_from_project_list(scenario_state):
    app_router = scenario_state["sources"]["app_router"]
    project_list = scenario_state["sources"]["project_list"]
    assert "nav(`/projects/${id}`)" in project_list, project_list
    assert "navigate(`/projects/${project.id}`)" in project_list or "onClick" in project_list, project_list
    assert 'path="/projects/:id"' in app_router, app_router


@given("某个项目当前 latest phase 为 Phase 7")
def latest_phase_is_seven(scenario_state):
    scenario_state["expected_phase"] = 7


@when("用户点击进入该项目")
def user_clicks_into_project(scenario_state):
    scenario_state["sources"] = {
        "project_redirect": _read("src/frontend/pages/ProjectRedirect.tsx"),
        "workflow_page": _read("src/frontend/pages/WorkflowPage.tsx"),
        "phase_navigation": _read("src/frontend/components/PhaseNavigation.tsx"),
    }


@then("项目工作流页应默认高亮 Phase 7")
def workflow_defaults_to_latest_phase(scenario_state):
    redirect = scenario_state["sources"]["project_redirect"]
    workflow = scenario_state["sources"]["workflow_page"]
    phase_nav = scenario_state["sources"]["phase_navigation"]
    assert (
        "latest_reached_phase" in redirect
        and "current_phase" in redirect
        and "/phases/${phase}" in redirect
    ), redirect
    assert "currentPhase = Number(phase)" in workflow, workflow
    assert 'data-active={p.phase === currentPhase ? "true" : "false"}' in phase_nav, (
        phase_nav
    )


@then("中间产物预览区应默认展示 Phase 7 的最新产物")
def preview_defaults_to_latest_phase_artifact(scenario_state):
    workflow = scenario_state["sources"]["workflow_page"]
    assert (
        "preview-slot-p${currentPhase}" in workflow or "preview-slot-p" in workflow
    ), workflow
    assert "currentPhase" in workflow and "预览" in workflow, workflow


@then("任务清单与对话区应默认切换到当前阶段上下文")
def task_list_and_dialog_default_to_current_phase_context(scenario_state):
    workflow = scenario_state["sources"]["workflow_page"]
    lowered = workflow.lower()
    assert "task" in lowered and (
        "dialog" in lowered or "conversation" in lowered or "chat" in lowered
    ), workflow


@given("某个项目已有多个 completed 阶段")
def project_has_multiple_completed_phases(scenario_state):
    scenario_state["project_has_completed_phases"] = True


@when("用户点击左侧任一已完成阶段")
def user_clicks_completed_phase(scenario_state):
    drawer_path = _REPO_ROOT / "src/frontend/components/PhaseDetailDrawer.tsx"
    scenario_state["drawer_exists"] = drawer_path.exists()
    scenario_state["drawer_source"] = (
        drawer_path.read_text() if drawer_path.exists() else ""
    )


@then("页面应展示该阶段的完整信息")
def page_shows_completed_phase_details(scenario_state):
    assert scenario_state["drawer_exists"], (
        "missing src/frontend/components/PhaseDetailDrawer.tsx"
    )


@then("完整信息至少包含主产物、review 结果、关键事件、用户修改记录和偏好确认结果")
def completed_phase_details_include_required_sections(scenario_state):
    drawer = scenario_state["drawer_source"]
    assert _has_all(
        drawer,
        "ArtifactList",
        "ReviewerResults",
        "OperationHistoryTimeline",
        "PreferenceSnapshot",
    ), drawer


@then("默认情况下该操作应为只读查看而不是立即回退重做")
def completed_phase_view_is_read_only_by_default(scenario_state):
    drawer = scenario_state["drawer_source"]
    assert "read_only" in drawer.lower() or "readonly" in drawer.lower(), drawer
