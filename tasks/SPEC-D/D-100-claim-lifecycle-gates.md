# [SPEC-D-100] 跨阶段 Claim 生命周期 + Gate-P8/P10/P11 阻断断言

## Metadata
- **task_id**: SPEC-D-100
- **spec_ref**: SPEC-D §D-BDD-1
- **depends_on**: [SPEC-C-103]
- **priority**: P0
- **estimated_complexity**: M

## Scope
在 P8/P10/P11 三个 Gate 中实现 claim 验证状态阻断逻辑，并在 P7/P8/P9 Phase Executor 中注入 claim_refs，确保未通过验证的硬性 claim 能在终审前阻断流程。

## Allowed Files
- `src/backend/engine/gate_checks/p8_claim_check.py`
- `src/backend/engine/gate_checks/p10_claim_check.py`
- `src/backend/engine/gate_checks/p11_claim_check.py`
- `src/backend/agents/phase_executors/p7_storyboard.py`
- `src/backend/agents/phase_executors/p8_keyframe.py`
- `src/backend/agents/phase_executors/p9_broll.py`
- `tests/integration/test_gate_claim_blocking.py`

## Acceptance Criteria
- [ ] AC-1: P8 shot 渲染前所有 claim_refs verified；失败则仅跳过该 shot
- [ ] AC-2: P10 合成前所有 hard blocking claims verified；否则 Gate FAIL
- [ ] AC-3: P11 终审同 P10
- [ ] AC-4: 人为留 1 个 unverified hard claim 时 Gate 返回 BLOCK + 告警事件

## Verification Commands
```bash
pytest tests/unit/pipeline/test_spec_d_100.py -v
```

## Completion Definition
P8/P10/P11 三个 Gate 在 claim 未验证时按规则阻断（P8 跳过单 shot，P10/P11 整体 FAIL），并发出告警事件，所有集成测试通过。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/pipeline/test_spec_d_100.py | test_p8_skips_shot_when_claim_unverified |
| AC-2 | tests/unit/pipeline/test_spec_d_100.py | test_p10_fails_on_unverified_hard_claim |
| AC-3 | tests/unit/pipeline/test_spec_d_100.py | test_p11_fails_on_unverified_hard_claim |
| AC-4 | tests/unit/pipeline/test_spec_d_100.py | test_gate_emits_block_alert_on_unverified_claim |
