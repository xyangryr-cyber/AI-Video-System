# [SPEC-G-011] Observability 断言格式对齐

## Metadata
- **task_id**: SPEC-G-011
- **spec_ref**: SPEC-G6.1, SPEC-G6.2
- **depends_on**: [SPEC-G-001]
- **priority**: P1
- **estimated_complexity**: XS
- **TDD 起点**: `observability.feature` 2 个 scenario 当前 FAIL（视为 RED）→ 修复 assertion 匹配 SUT 实际返回格式 → PASS（GREEN）

## Scope
Observability BDD 场景的 Then step 断言格式与 SUT 实际返回格式不一致:
1. "每次 agent 调用都必须留下四类证据" — 需要 DB 中有数据（G-001 解决），assertion 需要匹配 Observability 类方法实际返回格式
2. "敏感字段入库前必须脱敏" — `redact_text()` 函数正确但 test 期望 `sanitized_texts` key，格式不匹配

## Allowed Files
- `tests/integration/bdd/steps/observability_steps.py`

## Forbidden Files
- `src/backend/**` (SUT 功能正确，不修改)
- `src/frontend/**`
- `docs/specs/**`

## Acceptance Criteria
- [ ] AC-1: "每次 agent 调用都必须留下四类证据" → PASS
- [ ] AC-2: "敏感字段入库前必须脱敏" → PASS
- [ ] AC-3: `pytest tests/unit/ -q` 无回归（不修改 SUT）

## Verification Commands
```bash
pytest tests/integration/bdd/test_observability_bdd.py -v
ruff check tests/integration/bdd/steps/observability_steps.py
.venv/bin/python3 scripts/contracts/verify_no_skip_stubs.py
```

## Completion Definition
`observability.feature` 的 2 个失败场景均通过。完成后追加一行 commit 到 `PROGRESS.md`。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/integration/bdd/features/observability.feature | 每次 agent 调用都必须留下四类证据 |
| AC-2 | tests/integration/bdd/features/observability.feature | 敏感字段入库前必须脱敏 |
