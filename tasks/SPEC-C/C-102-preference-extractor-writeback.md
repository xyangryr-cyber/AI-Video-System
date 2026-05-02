# [SPEC-C-102] PreferenceExtractor stage scope + writeback API

## Metadata
- **task_id**: SPEC-C-102
- **spec_ref**: `SPEC-C` §C-BDD-3
- **depends_on**: [SPEC-A-101]
- **priority**: P0
- **estimated_complexity**: M
- **bdd_tags**: [@preferences, @preferences-2]

## Scope
扩展 PreferenceExtractor 支持 stage scope，新增 `/preferences/writeback-suggestions` API 返回 keep/update/add_stage_override 三类建议，并通过 STAGE_INJECTION_MATRIX 在运行时过滤偏好，避免阶段级偏好污染其他阶段。

## Allowed Files
- `src/backend/agents/preference_extractor.py`
- `src/backend/api/preferences.py`
- `src/backend/services/stage_preference_service.py`
- `tests/integration/test_preference_writeback.py`

## Acceptance Criteria
- [ ] AC-1: POST `/preferences/writeback-suggestions` 返回 `keep/update/add_stage_override` 三类建议
- [ ] AC-2: STAGE_INJECTION_MATRIX 运行时过滤通过单测
- [ ] AC-3: TTSAgent 底层切换为调用统一接口(v3.15 行为保持)
- [ ] AC-4: 阶段偏好污染其他阶段反例测试 FAIL

## Verification Commands
```bash
pytest tests/unit/backend-core/test_spec_c_102.py -v
```

## Completion Definition
writeback-suggestions API 返回三类建议、STAGE_INJECTION_MATRIX 过滤生效、TTSAgent 切换至统一接口且 v3.15 行为不变、跨阶段污染反例正确 FAIL，全部 AC 与集成测试通过。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/backend-core/test_spec_c_102.py | test_writeback_suggestions_returns_three_categories |
| AC-2 | tests/unit/backend-core/test_spec_c_102.py | test_stage_injection_matrix_runtime_filter |
| AC-3 | tests/unit/backend-core/test_spec_c_102.py | test_tts_agent_unified_interface_v315_parity |
| AC-4 | tests/unit/backend-core/test_spec_c_102.py | test_stage_preference_does_not_pollute_other_stages |
