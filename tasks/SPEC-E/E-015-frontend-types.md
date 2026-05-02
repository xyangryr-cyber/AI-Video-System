# [SPEC-E-015] 前端类型 MasterAudioView / AnnotationSpan / ShotMaterialBindingView / ChartMaterialView

## Metadata
- **task_id**: SPEC-E-015
- **spec_ref**: `docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md` §E-AUDP7A-5
- **delta_id**: TECH-DELTA-08
- **depends_on**: [SPEC-A-013, SPEC-A-014, SPEC-A-015, SPEC-A-016]
- **priority**: P0
- **estimated_complexity**: S

## Scope
在 `src/frontend/types/` 新增 4 类前端 View 类型，与 `src/shared/types/` 镜像；SPEC-11 前端类型契约表追加引用。若已配置 OpenAPI/JSON Schema → TS 自动生成，需跑通校验。

## Allowed Files
- `src/frontend/types/audio_master.ts` (NEW MasterAudioView)
- `src/frontend/types/annotation_span.ts` (NEW AnnotationSpan)
- `src/frontend/types/shot_material_binding.ts` (NEW ShotMaterialBindingView)
- `src/frontend/types/chart_material.ts` (NEW ChartMaterialView)
- `src/frontend/types/index.ts` (MODIFY 加 export)
- `tests/unit/frontend/types/test_v317_types_alignment.test.ts` (NEW)

## Forbidden Files
- `src/shared/**` (由 SPEC-A 维护)
- `src/backend/**`
- `src/frontend/components/**`
- `src/frontend/hooks/**`
- `src/frontend/store/**`
- `src/frontend/api/**`

## Acceptance Criteria
- [ ] AC-1：4 个 type 文件存在；`tsc --noEmit` 通过
- [ ] AC-2：与 `src/shared/types/` 对应文件字段一致（snapshot diff = 0；通过 ts-morph 或 reflect-types 工具校验）
- [ ] AC-3：自动生成（如配置 `npm run gen:types`）跑通且 diff 为空
- [ ] AC-4：types/index.ts 导出 4 个新类型，命名空间不与 v3.15/v3.16 既有冲突
- [ ] AC-5：MasterAudioView.kind 严格联合类型 'narration_master' | 'bgm_mix_master' | 'final_audio_master'，与后端枚举一致

## Verification Commands
```bash
npx tsc --noEmit src/frontend/types/audio_master.ts src/frontend/types/annotation_span.ts src/frontend/types/shot_material_binding.ts src/frontend/types/chart_material.ts
pytest tests/unit/frontend/test_spec_e_015.py -v
# 若有自动生成
npm run gen:types && git diff --exit-code src/frontend/types/
```

## Completion Definition
4 个类型 + index 导出 + 全部 5 条 AC PASS + 与 shared/types 一致。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/frontend/test_spec_e_015.py | files_exist_and_compile |
| AC-2 | tests/unit/frontend/test_spec_e_015.py | snapshot_match_shared_types |
| AC-3 | tests/unit/frontend/test_spec_e_015.py | autogen_diff_empty |
| AC-4 | tests/unit/frontend/test_spec_e_015.py | index_exports_no_namespace_conflict |
| AC-5 | tests/unit/frontend/test_spec_e_015.py | master_audio_kind_union_matches_backend |

## §23.9 验收门禁映射
- 第 10 行：前端字段可用（类型基础）
