# [SPEC-B-006] Preferences 表与存储一致性

## Metadata
- **task_id**: SPEC-B-006
- **spec_ref**: SPEC-12.1, SPEC-12.2, SPEC-12.3
- **depends_on**: [SPEC-A-xxx] (SPEC-1B DDL preferences 表, SPEC-1A preferences API), [SPEC-B-001]
- **priority**: P1
- **estimated_complexity**: M
- **bdd_tags**: [@preferences, @preferences-2]

## Scope
实现 `preferences` 表（project_id/global_rules_md/user_preferences_md/project_preferences_md/brand_kit_json/last_candidates_json/last_confirmed_at/updated_at）。新项目创建时自动插入行。偏好只写 SQLite，前端只从 API 读 SQLite。snapshot.md 为只读导出视图。恢复源为 `app.sqlite3.bak`，禁止从导出文件恢复。

## Allowed Files
- `src/backend/db/models/preferences.py`
- `src/backend/db/repositories/preferences_repo.py`
- `src/backend/api/routes/preferences.py`
- `src/backend/core/backup.py`
- `tests/unit/infra/test_preferences.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: 新项目创建后 `preferences` 表自动插入对应行
- [ ] AC-2: 偏好确认后 `last_confirmed_at` 更新
- [ ] AC-3: 修改 `snapshot.md` 后 API 返回值不变（只读导出验证）
- [ ] AC-4: 代码中无从 `snapshot.md` / `project_state.json` 写回 DB 的逻辑
- [ ] AC-5: `app.sqlite3.bak` 备份文件在数据目录中存在
- [ ] AC-6: 无从 `project_state.json` 恢复 DB 的逻辑

## Verification Commands
```bash
pytest tests/unit/infra/test_spec_b_006.py -v
sqlite3 data/db/app.sqlite3 ".schema preferences"
grep -rn "project_state.json" src/backend/ | grep -i "restore\|recover\|load"
```

## Completion Definition
preferences 表 DDL 正确，新项目自动初始化偏好行，写入/读取路径单一（只写 SQLite），备份恢复策略明确。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/infra/test_spec_b_006.py | test_auto_insert_on_project_create |
| AC-2 | tests/unit/infra/test_spec_b_006.py | test_last_confirmed_at_updated |
| AC-3 | tests/unit/infra/test_spec_b_006.py | test_snapshot_md_readonly |
| AC-4 | tests/unit/infra/test_spec_b_006.py | test_no_writeback_from_exports |
| AC-5 | tests/unit/infra/test_spec_b_006.py | test_sqlite_backup_exists |
