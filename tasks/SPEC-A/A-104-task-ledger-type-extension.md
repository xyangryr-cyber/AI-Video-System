# [SPEC-A-104] task_ledger.type 扩展至 BDD 动作

## Metadata
- **task_id**: SPEC-A-104
- **spec_ref**: `SPEC-A` §A-BDD-5(SPEC-1B `task_ledger` 表 type 枚举扩)
- **depends_on**: []
- **priority**: P0
- **estimated_complexity**: S

## Scope
扩展 task_ledger.type 枚举追加 6 种 BDD 动作(challenge_claim/supplement_claim/request_chart/view_phase_detail/save_stage_preference/insert_section),并补齐幂等规则与 DDL CHECK 约束,与 v3.15 既有 9 种合并为 15 种。

## Allowed Files
- `src/shared/constants/task_types.py`
- `src/shared/types/task_types.ts`
- `migrations/V{NNN}__extend_task_ledger_types.sql`
- `tests/unit/contracts/test_task_types.py`

## Acceptance Criteria
- [ ] AC-1: 枚举追加 6 值:`challenge_claim/supplement_claim/request_chart/view_phase_detail/save_stage_preference/insert_section`
- [ ] AC-2: 合并 v3.15 共 15 种;幂等规则表定义新 6 种的 idempotency key
- [ ] AC-3: CHECK 约束或迁移 trigger 校验枚举完整性

## Verification Commands
```bash
pytest tests/unit/contracts/test_spec_a_104.py -v
```

## Completion Definition
task_types 常量(Py + TS)、迁移脚本、幂等规则三件一致,新 6 类型可通过 DDL 校验且测试 GREEN。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/contracts/test_spec_a_104.py | test_task_ledger_type_enum_appends_six_bdd_actions |
| AC-2 | tests/unit/contracts/test_spec_a_104.py | test_task_types_total_fifteen_with_idempotency_keys_for_new_six |
| AC-3 | tests/unit/contracts/test_spec_a_104.py | test_migration_check_constraint_rejects_unknown_task_type |
