# [SPEC-B-014] 存储目录规范扩展（phase_5/6/7a 新增产物目录）

## Metadata
- **task_id**: SPEC-B-014
- **spec_ref**: `docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md` §B-AUDP7A-2
- **delta_id**: TECH-DELTA-02 / TECH-DELTA-03 / TECH-DELTA-05 / TECH-DELTA-06
- **depends_on**: [SPEC-A-013, SPEC-A-014, SPEC-A-015, SPEC-A-016]
- **priority**: P0
- **estimated_complexity**: S

## Scope
项目存储目录预创建规则 + 备份/清理策略：在 SPEC-1.2 / SPEC-1.3 / SPEC-15 追加 phase_5/bgm_candidates、phase_6/sfx_applied_segments、phase_7a/{verified_materials,chart_materials} 等新目录的预创建、归档、清理规则。

## Allowed Files
- `src/backend/infra/storage_layout.py` (MODIFY；项目初始化目录预创建)
- `src/backend/infra/cleanup_rules.py` (MODIFY；归档/清理白黑名单)
- `tests/unit/infra/test_storage_layout_v317.py` (NEW)
- `tests/unit/infra/test_cleanup_rules_v317.py` (NEW)
- `tests/fixtures/project_dirs/v317_layout/` (NEW 测试夹具)

## Forbidden Files
- `src/shared/**`
- `src/backend/services/**`
- `src/backend/agents/**`
- `src/backend/api/**`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1：项目初始化代码可预创建以下目录：phase_5/bgm_candidates、phase_6/sfx_applied_segments、phase_7a/、phase_7a/verified_materials、phase_7a/chart_materials
- [ ] AC-2：备份策略：phase_7a/verified_materials 标记为 OSS 异步归档；预览类（phase_5/bgm_mix_preview_*.mp3 / phase_6/sfx_applied_segments/）标记为本地 only
- [ ] AC-3：清理任务白名单：项目归档时保留 phase_4/narration_master.{mp3,json} / phase_5/bgm_mix_master.{mp3,json} / phase_6/final_audio_with_bgm_sfx.{mp3,json} / phase_7a/chart_materials/
- [ ] AC-4：清理任务黑名单：项目归档时删除 phase_5/bgm_candidates/ / phase_5/bgm_mix_preview_*.mp3 / phase_6/sfx_applied_segments/
- [ ] AC-5：单测覆盖：白/黑名单分类正确（构造夹具项目目录，归档后断言保留/删除文件集与预期一致）
- [ ] AC-6：v3.15 既有目录（phase_0..phase_11 的 v3.15 既有产物）不受影响（回归测试）

## Verification Commands
```bash
pytest tests/unit/infra/test_spec_b_014.py -v
# 集成：在临时项目上跑初始化 + 归档
python scripts/infra/test_archive_e2e.py --fixture v317_layout
```

## Completion Definition
预创建目录代码 + 清理规则代码就位 + 全部 6 条 AC 测试 PASS + 测试夹具完整 + v3.15 兼容回归通过。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/infra/test_spec_b_014.py | test_phase_5_bgm_candidates_created / test_phase_6_sfx_applied_segments_created / test_phase_7a_subdirs_created |
| AC-2 | tests/unit/infra/test_spec_b_014.py | test_oss_archive_includes_verified_materials / test_local_only_includes_previews |
| AC-3 | tests/unit/infra/test_spec_b_014.py | test_archive_keeps_master_audio_files / test_archive_keeps_chart_materials |
| AC-4 | tests/unit/infra/test_spec_b_014.py | test_archive_removes_bgm_candidates / test_archive_removes_sfx_applied_segments |
| AC-5 | tests/unit/infra/test_spec_b_014.py | test_archive_classification_end_to_end |
| AC-6 | tests/unit/infra/test_spec_b_014.py | test_v315_existing_dirs_intact |

## §23.9 验收门禁映射
- 第 1 / 5 / 7 / 8 行的产物落地物理基础
