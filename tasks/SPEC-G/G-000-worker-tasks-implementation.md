# [SPEC-G-000] Worker Tasks 实现 — 编排层 dispatch 链路落地

> **前置背景**: 这是 SPEC-G P-1 的落地 task。方案 A 已确认 (2026-04-25)。

## Metadata
- **task_id**: SPEC-G-000
- **spec_ref**: SPEC-G 前置架构决策 P-1
- **depends_on**: [SPEC-D-001..SPEC-D-026] (SPEC-D pipeline 全部 completion)
- **前置确认**: 实施前必须确认 SPEC-D 26 张 card 的实际完成状态（当前已验证: SPEC-D-013/D-018）。若 SPEC-D 还有未完成 card，仅未完成 card 涉及的 phase 的 worker task 可标记为 KNOWN_BLOCKED，其余 phase 的 task 注册不受阻。
- **priority**: P0 — 阻塞 G-002..G-007
- **estimated_complexity**: L+ (~200-400 行新代码)

## BDD Sync Dispatch Fixture 设计

BDD 测试在单进程 `:memory:` 环境中运行，无真实 Huey/Redis。需要同步执行路径使 `create_task()` 后 agent 方法被实际调用（而非仅写 pending 行）。

**方案**: `huey immediate=True` 模式 — 使用 Huey 的 `immediate` 模式让 task 在当前进程同步执行，无需 worker 进程或 Redis。

**Fixture 签名**:
```python
# tests/integration/bdd/conftest.py
@pytest.fixture
def bdd_dispatcher(bdd_db_conn):
    """提供同步 dispatch 能力的 Dispatcher，用于 BDD 测试。"""
    from huey import ImmediateHuey
    from src.backend.engine.dispatcher import Dispatcher
    huey = ImmediateHuey()
    return Dispatcher(conn=bdd_db_conn, huey=huey)

@pytest.fixture
def bdd_workflow_engine(bdd_db_conn, bdd_dispatcher):
    from src.backend.engine.workflow_engine import WorkflowEngine
    return WorkflowEngine(conn=bdd_db_conn, dispatcher=bdd_dispatcher)
```

**实现步骤**:
1. `Dispatcher.__init__` 接受可选 `huey` 参数（默认使用真实 Huey 实例）
2. `dispatch_once()` 在 pending→queued 后通过 `huey.enqueue()` 或 `huey()` 调起 task
3. BDD fixture 注入 `ImmediateHuey`，生产代码使用真实 Redis-backed Huey
4. 不新增独立的 "sync dispatcher" 类——通过参数化实现模式切换

## Scope
补齐 `src/backend/workers/tasks.py`，将 6 个 phase 的 agent 调用注册为 `@huey.task`，并修改 `Dispatcher.dispatch_once()` 在 pending→queued 后实际调起对应 worker task。这是 "SPEC-D pipeline 落地"——使 `WorkflowEngine.create_task()` 创建的任务最终能被 agent 实际执行。

**涉及的 6 个 phase**:

| Phase | task_type | 目标 Agent 方法 |
|-------|-----------|----------------|
| 4 | `generate_narration` | `TTSAgent.select_voice_candidates()` |
| 5 | `preview_mix` | `BGMAgent` / `AudioMixPreviewService` |
| 6 | `plan_layout` | `SFXAgent` / `SfxLayoutPlanner` |
| 8 | `render_keyframes` | `KeyframeRenderAgent.render_keyframes()` |
| 10 | `compose_rough_cut` | `RoughCutAgent.compose()` |
| 11 | `export_final` | `FinalCutAgent.adjust()` |

**Dispatcher 改造**:
- `dispatch_once()` 当前: pending→queued→return [task_id]
- 目标: pending→queued→按 `task_type` 路由到对应 huey task→记录到 `agent_call_log`/`events`
- BDD 测试模式: 需支持同步执行（单进程，无真实 Huey），在 fixture 层面可选 bypass

## Allowed Files
- `src/backend/workers/tasks.py`
- `src/backend/engine/dispatcher.py`

## To-Read (实现时参考)
- `src/backend/engine/dispatcher.py` (`dispatch_once`)
- `src/backend/engine/workflow_engine.py` (`create_task`, `update_task_status`)
- `src/backend/agents/tts_agent.py`
- `src/backend/agents/bgm_agent.py`
- `src/backend/agents/sfx_agent.py`
- `src/backend/agents/keyframe_render_agent.py`
- `src/backend/agents/rough_cut_agent.py`
- `src/backend/agents/final_cut_agent.py`
- `tests/integration/bdd/conftest.py` (BDD fixture 设计)

## Forbidden Files
- `src/frontend/**`
- `docs/specs/**`
- `HARNESS.md`
- `CLAUDE.md`

## Acceptance Criteria
- [ ] AC-1: `workers/tasks.py` 包含 6 个 `@huey.task` 注册函数，每个对应一个 phase
- [ ] AC-2: 每个 task 函数接收 `(project_id, phase, task_type, params)` 并路由到正确 agent 方法
- [ ] AC-3: `Dispatcher.dispatch_once()` 在 pending→queued 后调用对应 worker task
- [ ] AC-4: task 执行结果写入 `task_ledger.status` + `agent_call_log` + `events`
- [ ] AC-5: BDD `:memory:` 环境下可同步执行（不依赖真实 Huey/Redis），fixture 提供 bypass
- [ ] AC-6: `pytest tests/unit/ -q` 无回归 (保持 1100+ passed)
- [ ] AC-7: `ruff check` + `mypy` clean

## Verification Commands
```bash
pytest tests/unit/ -q
pytest tests/integration/bdd/features/phase4.feature -v  # G-002 的验证目标
ruff check src/backend/workers/tasks.py src/backend/engine/dispatcher.py
mypy src/backend/workers/tasks.py src/backend/engine/dispatcher.py
.venv/bin/python3 scripts/contracts/verify_no_skip_stubs.py
```

## Completion Definition
6 个 phase 的 worker task 已注册，`dispatch_once()` 可调起对应 agent。`create_task()` → agent 被实际调用 → `task_ledger`/`agent_call_log`/`events` 有记录。BDD 模式下（`:memory:` + sync bypass）`create_task()` 后 agent 方法被同步执行且结果可观测。完成后追加一行 commit 到 `PROGRESS.md`。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1-4 | tests/unit/pipeline/test_spec_d_004.py | worker task lookup + dispatch (existing + new) |
| AC-5 | tests/integration/bdd/conftest.py | sync dispatch fixture for BDD |
