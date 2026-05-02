# [SPEC-G-000d] Task → Agent 真实路由（业务逻辑）

> **来源**: G-000-DECOMPOSITION-HANDOFF.md §2 G-000d
> **顺序**: G-000c → **G-000d** → G-000e
> **注意**: 这是 G-000 拆解中**最大的一张子卡**（~250 行）。若实施 AI 评估单 context window 不够，可按 phase 进一步拆为 G-000d-p4 / d-p5 / d-p6 / d-p8 / d-p10 / d-p11。

## Metadata
- **task_id**: SPEC-G-000d
- **spec_ref**: SPEC-G P-1 + SPEC-D 对应 phase
- **depends_on**: [SPEC-G-000c]
- **priority**: P0
- **estimated_complexity**: L (~250 行)

## Scope
G-000c 的 6 个 task 函数现在抛 `NotImplementedError`。本卡把每个 task 函数实现为完整的 agent 调用流程:

1. 从 DB 读取 task 上下文（params + 项目状态）
2. 实例化对应 agent
3. 调用 agent 方法（按下方映射表）
4. 处理返回值 / 异常
5. 通过 `WorkflowEngine.update_task_status` 写终态（`succeeded` / `failed`）
6. **不**在 worker 内手动写 `events` 或 `agent_call_log`——这些由 G-000e 处理

### 各 Phase Agent 调用映射

| Phase | task 函数 | 主要 agent 方法 | params 必需字段 |
|-------|----------|---------------|----------------|
| 4 | `run_phase4_tts` | `TTSAgent().select_voice_candidates()` + `.build_timeline()` | `polished_script: dict`, `voice_preferences: dict?` |
| 5 | `run_phase5_bgm_preview` | `BGMAgent.produce_emotion_curve()` + `.select_bgm_candidates()` | `timeline: dict` |
| 6 | `run_phase6_sfx_layout` | `SFXAgent.produce_sfx()` + `.check_sparsity()` | `timeline: dict` |
| 8 | `run_phase8_keyframe` | `KeyframeRenderAgent().render_keyframes(storyboard=...)` + `.handle_failed_shot(...)` | `storyboard: list` |
| 10 | `run_phase10_rough_cut` | `RoughCutAgent.compose(...)` | （读 `rough_cut_agent.py` 完整签名后填） |
| 11 | `run_phase11_final_cut` | `FinalCutAgent.adjust(rough_cut_path=..., adjustments=...)` + `.run_audit_3()` | `rough_cut_path: str`, `adjustments: dict` |

### Worker 中获取 WorkflowEngine 的方式

**决策: 方案 A — 每次 task 执行时打开新 sqlite 连接**，传给 `WorkflowEngine(conn=...)`。简单、无状态、BDD immediate 模式下无污染风险。实施 AI 选方案 A，在 commit body 写明理由。

### 任务函数实现模板

```python
@huey.task()
def run_phase4_tts(task_id: str, params: dict) -> None:
    engine = get_workflow_engine()
    try:
        engine.update_task_status(task_id, "running", agent_name="TTSAgent")
        from src.backend.agents.tts_agent import TTSAgent
        agent = TTSAgent()
        result = agent.select_voice_candidates(
            polished_script=params["polished_script"],
            voice_preferences=params.get("voice_preferences"),
        )
        engine.update_task_status(task_id, "succeeded")
    except Exception as e:
        engine.update_task_status(
            task_id, "failed",
            error_code="AGENT_FAILURE",
            error_message=str(e)[:500],
        )
        raise
```

## Allowed Files
- `src/backend/workers/tasks.py`
- `tests/unit/workers/test_phase4_tasks.py`（新建）
- `tests/unit/workers/test_phase5_tasks.py`（新建）
- `tests/unit/workers/test_phase6_tasks.py`（新建）
- `tests/unit/workers/test_phase8_tasks.py`（新建）
- `tests/unit/workers/test_phase10_tasks.py`（新建）
- `tests/unit/workers/test_phase11_tasks.py`（新建）

## Forbidden Files
- 任何 agent 文件（**只读**，不改）
- `src/backend/engine/workflow_engine.py`（用其 API，不改）

## Acceptance Criteria

**每 phase 一组（共 6 × 3 = 18 项）**:

对每个 phase (4/5/6/8/10/11):
- [ ] AC-N.1: 成功路径: mock agent 返回成功值 → task 函数执行后 `task_ledger.status = succeeded`
- [ ] AC-N.2: 失败路径: mock agent 抛异常 → `task_ledger.status = failed`，`error_code = AGENT_FAILURE`
- [ ] AC-N.3: 参数透传: params 中的字段被正确传给 agent 方法

**通用**:
- [ ] AC-G.1: 无回归（unit baseline 通过数不降）
- [ ] AC-G.2: lint + mypy clean

## Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/workers/ -v
.venv/bin/python3 -m pytest tests/unit/ -q --tb=no | tail -3
.venv/bin/ruff check src/backend/workers/tasks.py
.venv/bin/mypy src/backend/workers/tasks.py
```

## Completion Definition
6 个 phase 的 task 函数均实现完整 agent 调用流程（成功 + 失败两条路径）。每个 phase 有独立单测文件覆盖成功/失败/参数透传。无回归。完成后追加一行 commit 记录到 `PROGRESS.md`（per HARNESS §9.2）。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-4.1 | tests/unit/workers/test_phase4_tasks.py | `test_phase4_success_path_sets_succeeded` |
| AC-4.2 | tests/unit/workers/test_phase4_tasks.py | `test_phase4_failure_path_sets_failed` |
| AC-4.3 | tests/unit/workers/test_phase4_tasks.py | `test_phase4_params_forwarded_to_agent` |
| AC-5.1 | tests/unit/workers/test_phase5_tasks.py | `test_phase5_success_path_sets_succeeded` |
| AC-5.2 | tests/unit/workers/test_phase5_tasks.py | `test_phase5_failure_path_sets_failed` |
| AC-5.3 | tests/unit/workers/test_phase5_tasks.py | `test_phase5_params_forwarded_to_agent` |
| AC-6.1 | tests/unit/workers/test_phase6_tasks.py | `test_phase6_success_path_sets_succeeded` |
| AC-6.2 | tests/unit/workers/test_phase6_tasks.py | `test_phase6_failure_path_sets_failed` |
| AC-6.3 | tests/unit/workers/test_phase6_tasks.py | `test_phase6_params_forwarded_to_agent` |
| AC-8.1 | tests/unit/workers/test_phase8_tasks.py | `test_phase8_success_path_sets_succeeded` |
| AC-8.2 | tests/unit/workers/test_phase8_tasks.py | `test_phase8_failure_path_sets_failed` |
| AC-8.3 | tests/unit/workers/test_phase8_tasks.py | `test_phase8_params_forwarded_to_agent` |
| AC-10.1 | tests/unit/workers/test_phase10_tasks.py | `test_phase10_success_path_sets_succeeded` |
| AC-10.2 | tests/unit/workers/test_phase10_tasks.py | `test_phase10_failure_path_sets_failed` |
| AC-10.3 | tests/unit/workers/test_phase10_tasks.py | `test_phase10_params_forwarded_to_agent` |
| AC-11.1 | tests/unit/workers/test_phase11_tasks.py | `test_phase11_success_path_sets_succeeded` |
| AC-11.2 | tests/unit/workers/test_phase11_tasks.py | `test_phase11_failure_path_sets_failed` |
| AC-11.3 | tests/unit/workers/test_phase11_tasks.py | `test_phase11_params_forwarded_to_agent` |

## TDD Path
建议每 phase 一个 RED-GREEN 循环（共 6 个），每个循环独立 commit:
1. `[SPEC-G-000d] RED: phase4 task → TTSAgent routing tests`
2. `[SPEC-G-000d] GREEN: phase4 task → TTSAgent routing`
3. ...（重复 6 次）
