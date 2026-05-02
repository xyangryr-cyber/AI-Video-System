# [SPEC-D-102] 局部插入 Scenario Cards + Gate-P2/P3 DiffAuditor 断言

## Metadata
- **task_id**: SPEC-D-102
- **spec_ref**: SPEC-D §D-BDD-3
- **depends_on**: [SPEC-C-104]
- **priority**: P0
- **estimated_complexity**: M

## Scope
实现 P2/P3 阶段 insert_section 的 Scenario Card 与对应 Gate 中的 DiffAuditor 校验，保证插入操作产生新 segment_id、与 regenerate_section 区分，并在 5% 阈值越界时正确拒绝。

## Allowed Files
- `src/backend/engine/scenario_cards/insert_section_p2_card.py`
- `src/backend/engine/scenario_cards/insert_section_p3_card.py`
- `src/backend/engine/gate_checks/p2_diff_auditor_check.py`
- `src/backend/engine/gate_checks/p3_diff_auditor_check.py`
- `tests/integration/test_insert_section_p2_p3.py`

## Acceptance Criteria
- [ ] AC-1: P2 insert_section 后 DiffAuditor.verdict=PASS 才进 Gate-P2
- [ ] AC-2: P3 同 P2
- [ ] AC-3: 与 regenerate_section 测试区分：新 segment_id 必产生
- [ ] AC-4: 5% 阈值恶意超出反例 FAIL

## Verification Commands
```bash
pytest tests/unit/pipeline/test_spec_d_102.py -v
```

## Completion Definition
P2/P3 insert_section Scenario Card 与 DiffAuditor Gate 集成完毕，新 segment_id 强制生成，超阈值反例正确 FAIL，所有集成测试通过。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/pipeline/test_spec_d_102.py | test_p2_insert_section_passes_with_diff_auditor_pass |
| AC-2 | tests/unit/pipeline/test_spec_d_102.py | test_p3_insert_section_passes_with_diff_auditor_pass |
| AC-3 | tests/unit/pipeline/test_spec_d_102.py | test_insert_section_generates_new_segment_id |
| AC-4 | tests/unit/pipeline/test_spec_d_102.py | test_insert_section_fails_when_exceeds_5pct_threshold |
