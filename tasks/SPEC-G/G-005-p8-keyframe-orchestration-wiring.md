# [SPEC-G-005] P8 Keyframe 阶段 BDD 编排层接线

## Metadata
- **task_id**: SPEC-G-005
- **spec_ref**: SPEC-G2.2 (P8 Keyframe)
- **depends_on**: [SPEC-G-001, SPEC-G-000e]
- **parallel_with**: [SPEC-G-002, SPEC-G-003, SPEC-G-004] — P8 与 P4-P6 音频链无数据依赖，可并行执行
- **priority**: P0
- **estimated_complexity**: M
- **TDD 起点**: `phase8.feature` 2 个 scenario 当前 FAIL（视为 RED）→ 重写 step definitions 走编排层 → scenario PASS（GREEN）

## Scope
重写 `tests/integration/bdd/steps/phase8_steps.py`，将直接调用 `KeyframeRenderAgent` 和 `VisualReviewer` 的 step definitions 改为通过编排层调用。P8 与 P4-P6 音频链并行，不依赖 G-002/003/004。

**文件大小预警**: 重写后需监控行数（HARNESS §6），2 个 scenario 的 step 预计 ~200 行。

## Allowed Files
- `tests/integration/bdd/steps/phase8_steps.py`
- `tests/integration/bdd/conftest.py`

## Forbidden Files
- `src/backend/agents/keyframe_render_agent.py`
- `src/backend/agents/visual_reviewer.py`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1: `phase8_steps.py` 不再直接 import `KeyframeRenderAgent` 或 `VisualReviewer`
- [ ] AC-2: "单个 shot 渲染失败时应局部降级而非整体失败" 通过 WorkflowEngine → KeyframeRenderAgent + `handle_failed_shot`（task_type="render_keyframes"）
- [ ] AC-3: "Gate 8 允许少量降级但要求总体成功率达标" 通过 WorkflowEngine → VisualReviewer + GateKeeper（task_type="render_keyframes"）
- [ ] AC-4: `pytest tests/unit/ -q` 无回归

## Verification Commands
```bash
pytest tests/integration/bdd/ -k "phase8" -v
pytest tests/unit/ -q
ruff check tests/integration/bdd/steps/phase8_steps.py tests/integration/bdd/conftest.py
mypy tests/integration/bdd/steps/phase8_steps.py
.venv/bin/python3 scripts/contracts/verify_no_skip_stubs.py
```

## Completion Definition
`phase8.feature` 全部 2 个 Scenario 通过。完成后追加一行 commit 到 `PROGRESS.md`。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-2 | tests/integration/bdd/features/phase8.feature | 单个 shot 渲染失败时应局部降级而非整体失败 |
| AC-3 | tests/integration/bdd/features/phase8.feature | Gate 8 允许少量降级但要求总体成功率达标 |
