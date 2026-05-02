# [SPEC-B-002] 持久化写路径单一性保障

## Metadata
- **task_id**: SPEC-B-002
- **spec_ref**: SPEC-1.2
- **depends_on**: [SPEC-A-xxx] (SPEC-1B DDL), [SPEC-B-001]
- **priority**: P0
- **estimated_complexity**: S

## Scope
确保所有结构化状态只写 SQLite（单一权威源）。媒体产物先写文件再提交 `artifact_ref` 到 DB。`snapshot.md` 和 `project_state.json` 为只读导出，禁止反向写回。实现孤儿文件清理机制（`artifact_ref` 提交失败时删除已写入的媒体文件）。

## Allowed Files
- `src/backend/core/storage.py`
- `src/backend/core/artifact_manager.py`
- `src/backend/db/repositories/*.py`
- `tests/unit/infra/test_write_path.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: 手动修改 `snapshot.md` → 重启 API → DB 值未被覆盖
- [ ] AC-2: `artifact_ref` 提交失败时孤儿文件被清理
- [ ] AC-3: 代码中无从 `project_state.json` 读取并写入 DB 的逻辑（grep 验证）
- [ ] AC-4: 所有 DB 写入操作集中在 repository 层，无分散写入

## Verification Commands
```bash
pytest tests/unit/infra/test_spec_b_002.py -v
grep -rn "project_state.json" src/backend/ | grep -v "export\|read_only\|dump"
grep -rn "snapshot.md" src/backend/ | grep -v "export\|generate\|write_snapshot"
```

## Completion Definition
通过单元测试验证 snapshot.md/project_state.json 修改不会回写 DB，孤儿文件清理逻辑可执行。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/infra/test_spec_b_002.py | test_snapshot_md_change_does_not_overwrite_db |
| AC-2 | tests/unit/infra/test_spec_b_002.py | test_orphan_file_cleanup_on_artifact_ref_failure |
| AC-3 | tests/unit/infra/test_spec_b_002.py | test_no_project_state_json_writeback |
