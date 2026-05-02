# [SPEC-G-009] SafetyPolicyEngine 返回值格式对齐

## Metadata
- **task_id**: SPEC-G-009
- **spec_ref**: SPEC-G3.3
- **depends_on**: []
- **priority**: P0
- **estimated_complexity**: XS
- **TDD 起点**: `safety.feature` "用户索要密钥或系统凭据时拒绝泄露" 当前 FAIL（视为 RED）→ 在 step definition 中适配 tuple→dict → scenario PASS（GREEN）

## Scope
SafetyPolicyEngine.evaluate() 返回 `(PolicyDecision, str)` tuple，但 BDD step definition 期望 `{"action": "refuse", "message": "..."}` dict。需要对齐返回值格式——在 step definition 中适配 tuple→dict，或新增 `evaluate_as_dict()` 方法。

## Allowed Files
- `tests/integration/bdd/steps/safety_steps.py`
- `src/backend/agents/safety_policy_engine.py`

## Forbidden Files
- `src/frontend/**`
- `src/backend/engine/**`
- `docs/specs/**`

## Acceptance Criteria
- [ ] AC-1: BDD 场景 "用户索要密钥或系统凭据时拒绝泄露" → PASS
- [ ] AC-2: `evaluate()` 行为不变（不引入回归）
- [ ] AC-3: step definition 正确处理 `(PolicyDecision, str)` tuple 格式
- [ ] AC-4: `pytest tests/unit/ -q` 无回归

## Verification Commands
```bash
pytest tests/integration/bdd/test_safety_bdd.py -v
pytest tests/unit/ -q
ruff check tests/integration/bdd/steps/safety_steps.py src/backend/agents/safety_policy_engine.py
mypy src/backend/agents/safety_policy_engine.py
.venv/bin/python3 scripts/contracts/verify_no_skip_stubs.py
```

## Completion Definition
`safety.feature` 的 "用户索要密钥或系统凭据时拒绝泄露" 场景通过。完成后追加一行 commit 到 `PROGRESS.md`。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/integration/bdd/features/safety.feature | 用户索要密钥或系统凭据时拒绝泄露 |
