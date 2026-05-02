# [SPEC-G-007] P11 FinalCut 阶段 BDD 编排层接线

## Metadata
- **task_id**: SPEC-G-007
- **spec_ref**: SPEC-G2.2 (P11 FinalCut)
- **depends_on**: [SPEC-G-001, SPEC-G-000e, SPEC-G-006]
- **priority**: P0
- **estimated_complexity**: M
- **TDD 起点**: `phase11.feature` 2 个 scenario 当前 FAIL（视为 RED）→ 重写 step → scenario PASS（GREEN）

## Scope
重写 `tests/integration/bdd/steps/phase11_steps.py`，将直接调用 `FinalCutAgent` 的 step definitions 改为通过编排层调用。P11 依赖 P10 的粗剪产物。

**文件大小预警**: 重写后需监控行数（HARNESS §6 限制 400 行）。

## Allowed Files
- `tests/integration/bdd/steps/phase11_steps.py`
- `tests/integration/bdd/conftest.py`

## Forbidden Files
- `src/backend/agents/final_cut_agent.py`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1: `phase11_steps.py` 不再直接 import `FinalCutAgent`
- [ ] AC-2: "最终交付必须覆盖所有目标平台" 通过 `WorkflowEngine.create_task(project_id=..., phase=11, task_type="export_final", params=...)` 调用（注意: `task_type` 不是 `action`，`params` 不是 `payload`）
- [ ] AC-3: "封面必须至少提供 3 个可选方案" 通过编排层返回至少 3 个候选封面
- [ ] AC-4: `pytest tests/unit/ -q` 无回归

## Verification Commands
```bash
pytest tests/integration/bdd/ -k "phase11" -v
pytest tests/unit/ -q
ruff check tests/integration/bdd/steps/phase11_steps.py tests/integration/bdd/conftest.py
mypy tests/integration/bdd/steps/phase11_steps.py
.venv/bin/python3 scripts/contracts/verify_no_skip_stubs.py
```

## Completion Definition
`phase11.feature` 全部 2 个 Scenario 通过。完成后追加一行 commit 到 `PROGRESS.md`。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-2 | tests/integration/bdd/features/phase11.feature | 最终交付必须覆盖所有目标平台 |
| AC-3 | tests/integration/bdd/features/phase11.feature | 封面必须至少提供 3 个可选方案 |
