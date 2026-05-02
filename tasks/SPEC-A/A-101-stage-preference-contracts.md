# [SPEC-A-101] StagePreference + STAGE_INJECTION_MATRIX

## Metadata
- **task_id**: SPEC-A-101
- **spec_ref**: `SPEC-A` §A-BDD-2(含 SPEC-0A.9)
- **depends_on**: []
- **priority**: P0
- **estimated_complexity**: S

## Scope
定义 StagePreference 跨语言契约与 STAGE_INJECTION_MATRIX 注入矩阵常量,覆盖 scope 优先级链(global/cross_project/project/stage)与各阶段(P4..P9)的注入 key 前缀,并提供 SQLAlchemy 模型 + DDL。

## Allowed Files
- `src/shared/schemas/stage_preference.py`
- `src/shared/types/stage_preference.ts`
- `src/shared/constants/stage_injection_matrix.py`
- `src/backend/models/stage_preference.py`
- `migrations/V{NNN}__create_stage_preferences.sql`
- `tests/unit/contracts/test_stage_preference.py`

## Acceptance Criteria
- [ ] AC-1: `StagePreference` schema 含 scope 枚举(`global/cross_project/project/stage`) + priority 校验
- [ ] AC-2: `STAGE_INJECTION_MATRIX` 常量定义 P4..P9 对应注入 key 前缀
- [ ] AC-3: DDL 创建 `stage_preferences` 表,unique(project_id, stage, key)
- [ ] AC-4: 单测覆盖优先级链 `stage > project > cross_project > user > global`
- [ ] AC-5: 单测覆盖"P5 偏好不注入 P4"反例

## Verification Commands
```bash
pytest tests/unit/contracts/test_spec_a_101.py -v
```

## Completion Definition
StagePreference schema、STAGE_INJECTION_MATRIX 常量、DDL 三件齐备,优先级链与跨阶段注入隔离均有测试覆盖且全部 GREEN。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/contracts/test_spec_a_101.py | test_stage_preference_scope_enum_and_priority_validation |
| AC-2 | tests/unit/contracts/test_spec_a_101.py | test_stage_injection_matrix_defines_p4_to_p9_prefixes |
| AC-3 | tests/unit/contracts/test_spec_a_101.py | test_migration_creates_stage_preferences_unique_constraint |
| AC-4 | tests/unit/contracts/test_spec_a_101.py | test_priority_chain_stage_over_project_over_cross_project_over_user_over_global |
| AC-5 | tests/unit/contracts/test_spec_a_101.py | test_stage_p5_bgm_not_injected_into_p4_tts |
