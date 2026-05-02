# [SPEC-B-013] SQLite 迁移：projects 表新增 master_audio_ref 列

## Metadata
- **task_id**: SPEC-B-013
- **spec_ref**: `docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md` §B-AUDP7A-1
- **delta_id**: TECH-DELTA-01
- **depends_on**: [SPEC-A-013]
- **priority**: P0
- **estimated_complexity**: S

## Scope
为 SPEC-A-013 在 ProjectState 引入的 `master_audio_ref` 字段创建 SQLite 迁移；同步 SPEC-1B projects 表 DDL 文档与表级读写归属表。

## Allowed Files
- `scripts/migrations/V0XX__add_master_audio_ref.sql` (NEW；XX = 当前最大编号 +1)
- `scripts/migrations/test_migration_master_audio_ref.py` (NEW migration 测试)
- `tests/unit/infra/test_projects_table_master_audio_ref.py` (NEW)

## Forbidden Files
- `src/shared/schemas/project_state.py` (由 A-013 维护)
- `src/shared/types/**`
- `src/backend/services/**`
- `src/backend/api/**`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1：迁移文件 forward 部分包含 `ALTER TABLE projects ADD COLUMN master_audio_ref TEXT` + 索引 `idx_projects_master_audio_phase` 基于 `json_extract(master_audio_ref, '$.based_on_phase')`
- [ ] AC-2：迁移文件 rollback 部分能完整还原（DROP INDEX + DROP COLUMN）
- [ ] AC-3：在测试 DB 上 `forward → rollback → forward` 序列幂等通过（重复 apply 不报错）
- [ ] AC-4：写入测试：插入合法 JSON `{"kind":"narration_master","file_path":"phase_4/narration_master.mp3","based_on_phase":4,"checksum":"sha256:...","version":1}`；读取后通过 A-013 schema 校验
- [ ] AC-5：CI 中迁移幂等性测试纳入 `tests/unit/infra/`，与既有迁移测试同等待遇
- [ ] AC-6：SPEC-1B 文档（`docs/specs/SPEC-A-contracts.md` 中 SPEC-1B 章节，由 SPEC-A 体系维护，本任务仅追加表级读写归属行：`master_audio_ref` 写入方=NarrationMasterAssembler/BgmMixRenderer/FinalAudioAssembler；读取方=前端主播放器/P7-P11 主音频消费者；写入时机=Gate 4/5/6 PASS）—— 通过文档 PR 同步，本任务仅产生迁移脚本 + 文档 diff hint

## Verification Commands
```bash
pytest tests/unit/infra/test_spec_b_013.py -v
# 集成迁移序列
python scripts/migrations/run_all.py --target-db data/db/test_master_audio_ref.sqlite3
sqlite3 data/db/test_master_audio_ref.sqlite3 "PRAGMA table_info(projects);" | grep master_audio_ref
```

## Completion Definition
迁移脚本就位 + forward/rollback/幂等三测全 PASS + 索引创建 + 写入读取 schema 校验通过 + 表级读写归属文档 hint 已记录。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | scripts/migrations/test_migration_master_audio_ref.py | test_forward_adds_column / test_forward_creates_index |
| AC-2 | scripts/migrations/test_migration_master_audio_ref.py | test_rollback_drops_column_and_index |
| AC-3 | scripts/migrations/test_migration_master_audio_ref.py | test_forward_rollback_forward_idempotent |
| AC-4 | tests/unit/infra/test_spec_b_013.py | test_insert_valid_master_audio_ref / test_read_back_passes_schema |
| AC-5 | tests/unit/infra/test_spec_b_013.py | test_migration_in_ci_unit_suite |
| AC-6 | tests/unit/infra/test_spec_b_013.py | test_table_level_ownership_hint_documented (读 SPEC-1B doc) |

## §23.9 验收门禁映射
- 第 1 行：`master_audio_ref` 迁移
