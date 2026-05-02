# [SPEC-G-006] P10 RoughCut 阶段 BDD 编排层接线

## Metadata
- **task_id**: SPEC-G-006
- **spec_ref**: SPEC-G2.2 (P10 RoughCut)
- **depends_on**: [SPEC-G-001, SPEC-G-000e, SPEC-G-002, SPEC-G-005] — P10 依赖 P4（音频产物）+ P8（关键帧产物）
- **priority**: P0
- **estimated_complexity**: M
- **TDD 起点**: `phase10.feature` "粗剪必须按时间轴拼接全部画面与音轨" 当前 FAIL（视为 RED）→ 重写 step → scenario PASS（GREEN）

## Scope
重写 `tests/integration/bdd/steps/phase10_steps.py`，将直接调用 `RoughCutAgent` 的 step definitions 改为通过编排层调用。P10 依赖 P4（音频）和 P8（关键帧）的产物，需要在编排层提供正确的 artifact 上下文。

**文件大小预警**: 重写后需监控行数（HARNESS §6 限制 400 行）。

## Allowed Files
- `tests/integration/bdd/steps/phase10_steps.py`
- `tests/integration/bdd/conftest.py`

## Forbidden Files
- `src/backend/agents/rough_cut_agent.py`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1: `phase10_steps.py` 不再直接 import `RoughCutAgent`
- [ ] AC-2: "粗剪必须按时间轴拼接全部画面与音轨" 通过 `WorkflowEngine.create_task(project_id=..., phase=10, task_type="compose_rough_cut", params=...)` 调用（注意: `task_type` 不是 `action`，`params` 不是 `payload`）
- [ ] AC-3: `pytest tests/unit/ -q` 无回归

## Verification Commands
```bash
pytest tests/integration/bdd/ -k "phase10" -v
pytest tests/unit/ -q
ruff check tests/integration/bdd/steps/phase10_steps.py tests/integration/bdd/conftest.py
mypy tests/integration/bdd/steps/phase10_steps.py
.venv/bin/python3 scripts/contracts/verify_no_skip_stubs.py
```

## Completion Definition
`phase10.feature` 的 "粗剪必须按时间轴拼接全部画面与音轨" 场景通过。完成后追加一行 commit 到 `PROGRESS.md`。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-2 | tests/integration/bdd/features/phase10.feature | 粗剪必须按时间轴拼接全部画面与音轨 |
