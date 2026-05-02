# [SPEC-G-003] P5 BGM 阶段 BDD 编排层接线

## Metadata
- **task_id**: SPEC-G-003
- **spec_ref**: SPEC-G2.2 (P5 BGM)
- **depends_on**: [SPEC-G-001, SPEC-G-000e, SPEC-G-002]
- **priority**: P0
- **estimated_complexity**: M
- **TDD 起点**: `phase5.feature` 2 个 scenario 当前 FAIL（视为 RED）→ 重写 step definitions 走编排层 → scenario PASS（GREEN）

## Scope
重写 `tests/integration/bdd/steps/phase5_steps.py`，将直接调用 `BGMAgent` 的 step definitions 改为通过编排层调用。BDD 场景"用户选择跳过背景音乐"和"用户试听时应听到混入 BGM 后的完整音频"当前因 step 直接调 agent stateless 方法而失败。

**文件大小预警**: 重写后需监控行数（HARNESS §6 限制 400 行），必要时拆分。

## Allowed Files
- `tests/integration/bdd/steps/phase5_steps.py`
- `tests/integration/bdd/conftest.py`

## Forbidden Files
- `src/backend/agents/bgm_agent.py`
- `src/backend/engine/gatekeeper.py` (GateKeeper 实现正确——GateP5 用 GateKeeper 回退在 BDD 层面可接受)
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1: `phase5_steps.py` 不再直接 import `BGMAgent`
- [ ] AC-2: "用户选择跳过背景音乐" 场景通过 GateKeeper skip 分支（task_type="preview_mix"）
- [ ] AC-3: "用户试听时应听到混入 BGM 后的完整音频" 场景调用 `AudioMixPreviewService` 走 WorkflowEngine（task_type="preview_mix"）
- [ ] AC-4: `pytest tests/unit/ -q` 无回归

## Verification Commands
```bash
pytest tests/integration/bdd/ -k "phase5" -v
pytest tests/unit/ -q
ruff check tests/integration/bdd/steps/phase5_steps.py tests/integration/bdd/conftest.py
mypy tests/integration/bdd/steps/phase5_steps.py
.venv/bin/python3 scripts/contracts/verify_no_skip_stubs.py
```

## Completion Definition
`phase5.feature` 全部 2 个 Scenario 通过。Step definitions 走编排层路径。完成后追加一行 commit 到 `PROGRESS.md`。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-2 | tests/integration/bdd/features/phase5.feature | 用户选择跳过背景音乐 |
| AC-3 | tests/integration/bdd/features/phase5.feature | 用户试听时应听到混入 BGM 后的完整音频 |
