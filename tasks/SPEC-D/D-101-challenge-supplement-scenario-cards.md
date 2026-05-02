# [SPEC-D-101] 用户质疑 / 补充 Phase Scenario Cards

## Metadata
- **task_id**: SPEC-D-101
- **spec_ref**: SPEC-D §D-BDD-2
- **depends_on**: [SPEC-C-101, SPEC-C-103]
- **priority**: P0
- **estimated_complexity**: M

## Scope
实现用户对 claim 提出质疑（challenge）与补充（supplement）的两类 Scenario Card，配套 artifact damage 标记服务，确保下游产物在 SLA 内被正确标记并阻断，且具备幂等性与双版本保留能力。

## Allowed Files
- `src/backend/engine/scenario_cards/challenge_claim_card.py`
- `src/backend/engine/scenario_cards/supplement_claim_card.py`
- `src/backend/services/artifact_damage_marker.py`
- `tests/integration/test_challenge_supplement_flow.py`

## Acceptance Criteria
- [ ] AC-1: challenge_claim 后 60s SLA 内下游 artifacts 标 damaged
- [ ] AC-2: supplement_claim 后新 claim 入队且下游阻断
- [ ] AC-3: 幂等规则：同 claim_id + evidence_hash 24h 内第二次质疑被丢弃
- [ ] AC-4: 复验两版结果不一致时保留双 verification_record

## Verification Commands
```bash
pytest tests/unit/pipeline/test_spec_d_101.py -v
```

## Completion Definition
challenge / supplement 两类 Scenario Card 落地，下游 artifact damage 标记在 SLA 内完成，幂等与双版本保留规则均通过集成测试验证。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/pipeline/test_spec_d_101.py | test_challenge_marks_downstream_damaged_within_sla |
| AC-2 | tests/unit/pipeline/test_spec_d_101.py | test_supplement_enqueues_new_claim_and_blocks |
| AC-3 | tests/unit/pipeline/test_spec_d_101.py | test_challenge_idempotency_within_24h |
| AC-4 | tests/unit/pipeline/test_spec_d_101.py | test_dual_verification_record_on_conflict |
