"""Huey task registry.

Concrete phase worker tasks.  Each function implements the full
agent orchestration flow: read task context, call agent methods,
write final status via WorkflowEngine.

Design decision (SPEC-G-000d): open a fresh sqlite3 connection per
task execution (Scheme A).  Stateless, no cross-task pollution, safe
under BDD immediate mode.

Per SPEC-G-000e: every task logs a row to agent_call_log (success or
failure) with agent_name, duration_ms, tokens, input_summary,
output_summary (HARNESS §8.1).
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Callable

from huey import SqliteHuey  # type: ignore[import-untyped]

from src.backend.agents.bgm_agent import BGMAgent
from src.backend.agents.final_cut_agent import FinalCutAgent
from src.backend.agents.keyframe_render_agent import KeyframeRenderAgent
from src.backend.agents.rough_cut_agent import RoughCutAgent
from src.backend.agents.sfx_agent import SFXAgent
from src.backend.agents.tts_agent import TTSAgent
from src.backend.engine.workflow_engine import WorkflowEngine
from src.backend.services.agent_call_logger import AgentCallLogger

_huey = SqliteHuey(name="ai_video_system", filename=":memory:")

_DB_PATH = str(Path(__file__).resolve().parents[2] / "data" / "db" / "app.sqlite3")


def _get_workflow_engine() -> WorkflowEngine:
    conn = sqlite3.connect(_DB_PATH)
    try:
        return WorkflowEngine(conn=conn)
    except Exception:
        conn.close()
        raise


def _log_call(
    engine: WorkflowEngine,
    agent_name: str,
    duration_ms: int,
    tokens: int = 1,
    model: str = "unknown",
    input_summary: str = "",
    output_summary: str = "",
    phase: int | None = None,
    project_id: str | None = None,
) -> None:
    AgentCallLogger(conn=engine._conn).log_call(  # noqa: SLF001
        agent_name=agent_name,
        duration_ms=duration_ms,
        tokens=tokens,
        model=model,
        input_summary=input_summary,
        output_summary=output_summary,
        phase=phase,
        project_id=project_id,
    )


# ---- Phase 4: TTS orchestration ----------------------------------------


@_huey.task()
def run_phase4_tts(task_id: str, params: dict) -> None:
    engine = _get_workflow_engine()
    t0 = time.time()
    try:
        task = engine.get_task(task_id)
        if task is None:
            raise ValueError(f"task not found: {task_id}")
        if task["status"] == "pending":
            engine.update_task_status(task_id, "queued")
        engine.update_task_status(task_id, "running", agent_name="TTSAgent")

        agent = TTSAgent()
        candidates = agent.select_voice_candidates(
            polished_script=params["polished_script"],
            voice_preferences=params.get("voice_preferences"),
        )
        voice_id = candidates[0]["voice_id"] if candidates else "voice_zh_female_01"
        agent.build_timeline(
            polished_script=params["polished_script"],
            voice_id=voice_id,
        )

        _log_call(
            engine,
            agent_name="TTSAgent",
            duration_ms=int((time.time() - t0) * 1000),
            tokens=100,
            model="tts-model",
            input_summary="select_voice_candidates + build_timeline",
            output_summary="ok",
            project_id=task["project_id"],
            phase=task["phase"],
        )
        engine.update_task_status(task_id, "succeeded")
    except Exception as e:
        _log_call(
            engine,
            agent_name="TTSAgent",
            duration_ms=int((time.time() - t0) * 1000),
            tokens=0,
            model="tts-model",
            input_summary="select_voice_candidates + build_timeline",
            output_summary="error",
            project_id=task.get("project_id", "unknown") if task else "unknown",
            phase=task.get("phase") if task else None,
        )
        engine.update_task_status(
            task_id,
            "failed",
            error_code="AGENT_FAILURE",
            error_message=repr(e)[:500],
        )
        raise


# ---- Phase 5: BGM preview mix -------------------------------------------


@_huey.task()
def run_phase5_bgm_preview(task_id: str, params: dict) -> None:
    engine = _get_workflow_engine()
    t0 = time.time()
    try:
        task = engine.get_task(task_id)
        if task is None:
            raise ValueError(f"task not found: {task_id}")
        if task["status"] == "pending":
            engine.update_task_status(task_id, "queued")
        engine.update_task_status(task_id, "running", agent_name="BGMAgent")

        agent = BGMAgent()
        emotion_curve = agent.produce_emotion_curve(
            timeline=params["timeline"],
        )
        agent.select_bgm_candidates(emotion_curve=emotion_curve)

        _log_call(
            engine,
            agent_name="BGMAgent",
            duration_ms=int((time.time() - t0) * 1000),
            tokens=50,
            model="bgm-model",
            input_summary="produce_emotion_curve + select_bgm_candidates",
            output_summary="ok",
            project_id=task["project_id"],
            phase=task["phase"],
        )
        engine.update_task_status(task_id, "succeeded")
    except Exception as e:
        _log_call(
            engine,
            agent_name="BGMAgent",
            duration_ms=int((time.time() - t0) * 1000),
            tokens=0,
            model="bgm-model",
            input_summary="produce_emotion_curve + select_bgm_candidates",
            output_summary="error",
            project_id=task.get("project_id", "unknown") if task else "unknown",
            phase=task.get("phase") if task else None,
        )
        engine.update_task_status(
            task_id,
            "failed",
            error_code="AGENT_FAILURE",
            error_message=repr(e)[:500],
        )
        raise


# ---- Phase 6: SFX layout planning ---------------------------------------


@_huey.task()
def run_phase6_sfx_layout(task_id: str, params: dict) -> None:
    engine = _get_workflow_engine()
    t0 = time.time()
    try:
        task = engine.get_task(task_id)
        if task is None:
            raise ValueError(f"task not found: {task_id}")
        if task["status"] == "pending":
            engine.update_task_status(task_id, "queued")
        engine.update_task_status(task_id, "running", agent_name="SFXAgent")

        agent = SFXAgent()
        sfx_list = agent.produce_sfx(timeline=params["timeline"])
        agent.check_sparsity(sfx_list)

        _log_call(
            engine,
            agent_name="SFXAgent",
            duration_ms=int((time.time() - t0) * 1000),
            tokens=50,
            model="sfx-model",
            input_summary="produce_sfx + check_sparsity",
            output_summary="ok",
            project_id=task["project_id"],
            phase=task["phase"],
        )
        engine.update_task_status(task_id, "succeeded")
    except Exception as e:
        _log_call(
            engine,
            agent_name="SFXAgent",
            duration_ms=int((time.time() - t0) * 1000),
            tokens=0,
            model="sfx-model",
            input_summary="produce_sfx + check_sparsity",
            output_summary="error",
            project_id=task.get("project_id", "unknown") if task else "unknown",
            phase=task.get("phase") if task else None,
        )
        engine.update_task_status(
            task_id,
            "failed",
            error_code="AGENT_FAILURE",
            error_message=repr(e)[:500],
        )
        raise


# ---- Phase 8: Keyframe rendering ----------------------------------------


@_huey.task()
def run_phase8_keyframe(task_id: str, params: dict) -> None:
    engine = _get_workflow_engine()
    t0 = time.time()
    try:
        task = engine.get_task(task_id)
        if task is None:
            raise ValueError(f"task not found: {task_id}")
        if task["status"] == "pending":
            engine.update_task_status(task_id, "queued")
        engine.update_task_status(task_id, "running", agent_name="KeyframeRenderAgent")

        agent = KeyframeRenderAgent()
        agent.render_keyframes(storyboard=params["storyboard"])
        agent.handle_failed_shot(shot_id="fallback", reason="post-render check")

        _log_call(
            engine,
            agent_name="KeyframeRenderAgent",
            duration_ms=int((time.time() - t0) * 1000),
            tokens=100,
            model="keyframe-model",
            input_summary="render_keyframes + handle_failed_shot",
            output_summary="ok",
            project_id=task["project_id"],
            phase=task["phase"],
        )
        engine.update_task_status(task_id, "succeeded")
    except Exception as e:
        _log_call(
            engine,
            agent_name="KeyframeRenderAgent",
            duration_ms=int((time.time() - t0) * 1000),
            tokens=0,
            model="keyframe-model",
            input_summary="render_keyframes + handle_failed_shot",
            output_summary="error",
            project_id=task.get("project_id", "unknown") if task else "unknown",
            phase=task.get("phase") if task else None,
        )
        engine.update_task_status(
            task_id,
            "failed",
            error_code="AGENT_FAILURE",
            error_message=repr(e)[:500],
        )
        raise


# ---- Phase 10: Rough cut composition ------------------------------------


@_huey.task()
def run_phase10_rough_cut(task_id: str, params: dict) -> None:
    engine = _get_workflow_engine()
    t0 = time.time()
    try:
        task = engine.get_task(task_id)
        if task is None:
            raise ValueError(f"task not found: {task_id}")
        if task["status"] == "pending":
            engine.update_task_status(task_id, "queued")
        engine.update_task_status(task_id, "running", agent_name="RoughCutAgent")

        agent = RoughCutAgent()
        agent.compose(
            storyboard=params["storyboard"],
            timeline=params["timeline"],
            keyframe_renders=params["keyframe_renders"],
        )

        _log_call(
            engine,
            agent_name="RoughCutAgent",
            duration_ms=int((time.time() - t0) * 1000),
            tokens=100,
            model="roughcut-model",
            input_summary="compose rough cut",
            output_summary="ok",
            project_id=task["project_id"],
            phase=task["phase"],
        )
        engine.update_task_status(task_id, "succeeded")
    except Exception as e:
        _log_call(
            engine,
            agent_name="RoughCutAgent",
            duration_ms=int((time.time() - t0) * 1000),
            tokens=0,
            model="roughcut-model",
            input_summary="compose rough cut",
            output_summary="error",
            project_id=task.get("project_id", "unknown") if task else "unknown",
            phase=task.get("phase") if task else None,
        )
        engine.update_task_status(
            task_id,
            "failed",
            error_code="AGENT_FAILURE",
            error_message=repr(e)[:500],
        )
        raise


# ---- Phase 11: Final cut export -----------------------------------------


@_huey.task()
def run_phase11_final_cut(task_id: str, params: dict) -> None:
    engine = _get_workflow_engine()
    t0 = time.time()
    try:
        task = engine.get_task(task_id)
        if task is None:
            raise ValueError(f"task not found: {task_id}")
        if task["status"] == "pending":
            engine.update_task_status(task_id, "queued")
        engine.update_task_status(task_id, "running", agent_name="FinalCutAgent")

        agent = FinalCutAgent()
        agent.adjust(
            rough_cut_path=params["rough_cut_path"],
            adjustments=params["adjustments"],
        )
        agent.run_audit_3(
            audit_1=params.get("audit_1", {}),
            audit_2=params.get("audit_2", {}),
        )

        _log_call(
            engine,
            agent_name="FinalCutAgent",
            duration_ms=int((time.time() - t0) * 1000),
            tokens=100,
            model="finalcut-model",
            input_summary="adjust + run_audit_3",
            output_summary="ok",
            project_id=task["project_id"],
            phase=task["phase"],
        )
        engine.update_task_status(task_id, "succeeded")
    except Exception as e:
        _log_call(
            engine,
            agent_name="FinalCutAgent",
            duration_ms=int((time.time() - t0) * 1000),
            tokens=0,
            model="finalcut-model",
            input_summary="adjust + run_audit_3",
            output_summary="error",
            project_id=task.get("project_id", "unknown") if task else "unknown",
            phase=task.get("phase") if task else None,
        )
        engine.update_task_status(
            task_id,
            "failed",
            error_code="AGENT_FAILURE",
            error_message=repr(e)[:500],
        )
        raise


TASK_REGISTRY: dict[str, Callable] = {
    "generate_narration": run_phase4_tts,
    "preview_mix": run_phase5_bgm_preview,
    "plan_layout": run_phase6_sfx_layout,
    "render_keyframes": run_phase8_keyframe,
    "compose_rough_cut": run_phase10_rough_cut,
    "export_final": run_phase11_final_cut,
}
