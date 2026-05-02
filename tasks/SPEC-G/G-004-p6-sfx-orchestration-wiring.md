# [SPEC-G-004] P6 SFX 阶段 BDD 编排层接线

## Metadata
- **task_id**: SPEC-G-004
- **spec_ref**: SPEC-G2.2 (P6 SFX)
- **depends_on**: [SPEC-G-001, SPEC-G-000e, SPEC-G-003]
- **priority**: P0
- **estimated_complexity**: M
- **TDD 起点**: `phase6.feature` 3 个 scenario 当前 FAIL（视为 RED）→ 重写 step definitions 走编排层 → scenario PASS（GREEN）

## Scope
重写 `tests/integration/bdd/steps/phase6_steps.py`，将直接调用 `SFXAgent` 的 step definitions 改为通过编排层调用。3 个 BDD 场景当前因 step 直接调 agent stateless 方法而失败。

**文件大小预警**: `phase6_steps.py` 3 个 scenario 重写后可能超过 400 行，需监控（HARNESS §6），必要时拆分为 `phase6_steps/` 子模块。

## Allowed Files
- `tests/integration/bdd/steps/phase6_steps.py`
- `tests/integration/bdd/conftest.py`

## Forbidden Files
- `src/backend/agents/sfx_agent.py`
- `src/backend/services/sfx_layout_planner.py`
- `src/backend/services/sfx_segment_mix_service.py`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1: `phase6_steps.py` 不再直接 import `SFXAgent`
- [ ] AC-2: "音效设计前应先基于全文脚本给出全局关键词布局与理由" 通过 WorkflowEngine → SfxLayoutPlanner（task_type="plan_layout"）
- [ ] AC-3: "前端应以全文标注形式展示全局音效布局" 通过编排层返回 annotation view 格式（task_type="plan_layout"）
- [ ] AC-4: "用户确认布局后系统应按编号分段加工音频并支持逐段试听" 通过 WorkflowEngine → SfxSegmentMixService（task_type="plan_layout"）
- [ ] AC-5: `pytest tests/unit/ -q` 无回归

## Verification Commands
```bash
pytest tests/integration/bdd/features/phase6.feature -v
pytest tests/unit/ -q
ruff check tests/integration/bdd/steps/phase6_steps.py tests/integration/bdd/conftest.py
mypy tests/integration/bdd/steps/phase6_steps.py
.venv/bin/python3 scripts/contracts/verify_no_skip_stubs.py
```

## Completion Definition
`phase6.feature` 全部 3 个 Scenario 通过。完成后追加一行 commit 到 `PROGRESS.md`。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-2 | tests/integration/bdd/features/phase6.feature | 音效设计前应先基于全文脚本给出全局关键词布局与理由 |
| AC-3 | tests/integration/bdd/features/phase6.feature | 前端应以全文标注形式展示全局音效布局 |
| AC-4 | tests/integration/bdd/features/phase6.feature | 用户确认布局后系统应按编号分段加工音频并支持逐段试听 |
