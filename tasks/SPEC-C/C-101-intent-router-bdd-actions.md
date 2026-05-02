# [SPEC-C-101] IntentRouter 6 个新 action

## Metadata
- **task_id**: SPEC-C-101
- **spec_ref**: `SPEC-C` §C-BDD-2
- **depends_on**: [SPEC-A-104, SPEC-C-100]
- **priority**: P0
- **estimated_complexity**: M

## Scope
扩展 IntentRouter 的 action 表，新增 6 个 v3.16 action（challenge_claim、supplement_claim、request_chart、view_phase_detail、save_stage_preference、insert_section），通过 SafetyGuard 前置控制 + Pydantic 校验 + claim 级 24h 幂等键，确保只有安全放行后的请求才进入 Router 分发。

## Allowed Files
- `src/backend/agents/intent_router.py`
- `src/backend/agents/actions/challenge_claim.py`
- `src/backend/agents/actions/supplement_claim.py`
- `src/backend/agents/actions/request_chart.py`
- `src/backend/agents/actions/view_phase_detail.py`
- `src/backend/agents/actions/save_stage_preference.py`
- `src/backend/agents/actions/insert_section.py`
- `tests/unit/agents/test_intent_router_v316.py`

## Acceptance Criteria
- [ ] AC-1: 6 新 action schema 全部通过 pydantic 校验
- [ ] AC-2: 幂等键规则覆盖(同 claim_id + evidence_hash 24h 幂等)
- [ ] AC-3: SafetyGuard allow/clarify 才允许进入 Router;refuse 测试断言 Router 未被调用

## Verification Commands
```bash
pytest tests/unit/backend-core/test_spec_c_101.py -v
```

## Completion Definition
6 个新 action 的 Pydantic schema 校验通过、claim_id+evidence_hash 24h 幂等键生效、SafetyGuard refuse 路径下 Router 不被调用，全部 AC 与单测通过。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/backend-core/test_spec_c_101.py | test_six_new_action_schemas_pydantic_valid |
| AC-2 | tests/unit/backend-core/test_spec_c_101.py | test_idempotency_key_claim_id_evidence_hash_24h |
| AC-3 | tests/unit/backend-core/test_spec_c_101.py | test_safety_refuse_blocks_router_invocation |
