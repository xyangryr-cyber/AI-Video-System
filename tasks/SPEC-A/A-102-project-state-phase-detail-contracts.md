# [SPEC-A-102] ProjectState.latest_reached_phase + PhaseDetailView contracts

## Metadata
- **task_id**: SPEC-A-102
- **spec_ref**: `SPEC-A` §A-BDD-3(SPEC-0A.3 扩字段 + SPEC-0A.10 新增)
- **depends_on**: []
- **priority**: P0
- **estimated_complexity**: M

## Scope
扩展 ProjectState 增加 latest_reached_phase 字段,并新增 PhaseDetailView 契约(七分块 + phase_history 时序 + read_only 标志),覆盖跨语言 schema 与历史数据回填迁移。

## Allowed Files
- `src/shared/schemas/project_state.py`
- `src/shared/types/project_state.ts`
- `src/shared/schemas/phase_detail_view.py`
- `src/shared/types/phase_detail_view.ts`
- `migrations/V{NNN}__add_latest_reached_phase.sql`
- `tests/unit/contracts/test_project_state_v316.py`
- `tests/unit/contracts/test_phase_detail_view_schema.py`

## Acceptance Criteria
- [ ] AC-1: 迁移后既有 project 的 `latest_reached_phase = current_phase`(回填兼容)
- [ ] AC-2: `PhaseDetailView` 含 7 分块(artifacts/reviewer_results/gate_result/claim_snapshot/preference_snapshot/diff_with_previous_version/operation_history)
- [ ] AC-3: `phase_history[]` 每条含 reached_at/completed_at?/last_revision_at?
- [ ] AC-4: `read_only` 布尔字段默认 true(历史阶段),current_phase 对应为 false

## Verification Commands
```bash
pytest tests/unit/contracts/test_spec_a_102.py -v
```

## Completion Definition
ProjectState 扩字段与 PhaseDetailView 新契约在 Pydantic/TS 两侧定义一致,迁移脚本完成回填,所有列出的测试 GREEN。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/contracts/test_spec_a_102.py | test_migration_backfills_latest_reached_phase_from_current_phase |
| AC-2 | tests/unit/contracts/test_spec_a_102.py | test_phase_detail_view_contains_seven_sections |
| AC-3 | tests/unit/contracts/test_spec_a_102.py | test_phase_history_entries_carry_reached_completed_revision_timestamps |
| AC-4 | tests/unit/contracts/test_spec_a_102.py | test_read_only_defaults_true_for_history_false_for_current_phase |
