# [SPEC-C-105] ChartIntentEngine 8 状态机

## Metadata
- **task_id**: SPEC-C-105
- **spec_ref**: `SPEC-C` §C-BDD-6
- **depends_on**: [SPEC-A-103, SPEC-C-103]
- **priority**: P0
- **estimated_complexity**: L

## Scope
实现 ChartIntentEngine 8 状态机，通过 property-based 测试验证任意随机转换序列都不违反合法边；澄清字段优先级 time_range/granularity > entity > unit/comparison；awaiting_verification 必须等所有 chart-bound claims verified 才进入 awaiting_confirmation；数据源不可用直接进入 failed 而非 rendering。

## Allowed Files
- `src/backend/agents/chart_intent_engine.py`
- `src/backend/services/chart_axis_generator.py`
- `tests/unit/agents/test_chart_state_machine.py`

## Acceptance Criteria
- [ ] AC-1: 8 状态 property-based 测试:任意随机转换序列不违反合法边
- [ ] AC-2: 澄清字段优先级:time_range/granularity > entity > unit/comparison
- [ ] AC-3: awaiting_verification 等所有 chart-bound claims verified 才进 awaiting_confirmation
- [ ] AC-4: 数据源不可用 → failed,不进入 rendering

## Verification Commands
```bash
pytest tests/unit/backend-core/test_spec_c_105.py -v
```

## Completion Definition
ChartIntentEngine 8 状态 property-based 转换合法、澄清字段优先级正确、awaiting_verification 在所有 chart-bound claims verified 后才推进、数据源不可用直接转 failed，全部 AC 与 property-based 单测通过。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/backend-core/test_spec_c_105.py | test_property_based_transitions_respect_legal_edges |
| AC-2 | tests/unit/backend-core/test_spec_c_105.py | test_clarification_field_priority_order |
| AC-3 | tests/unit/backend-core/test_spec_c_105.py | test_awaiting_verification_waits_all_chart_bound_claims |
| AC-4 | tests/unit/backend-core/test_spec_c_105.py | test_unavailable_data_source_transitions_to_failed |
