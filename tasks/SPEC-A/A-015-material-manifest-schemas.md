# [SPEC-A-015] MaterialManifest + ShotMaterialBindings schemas（P7A 物料清单契约）

## Metadata
- **task_id**: SPEC-A-015
- **spec_ref**: `docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md` §A-AUDP7A-3
- **delta_id**: PRD-DELTA-06 / TECH-DELTA-05
- **depends_on**: []
- **priority**: P0
- **estimated_complexity**: M

## Scope
新增两份 schema 把"分镜物料补充"作为 P7→P8 之间的中间 contract，含物料清单（material_manifest.json）+ shot 绑定表（shot_material_bindings.json），落入 SPEC-0A.1 artifact registry。

## Allowed Files
- `src/shared/schemas/material_manifest.py` (NEW Pydantic)
- `src/shared/types/material_manifest.ts` (NEW TS)
- `schemas/material_manifest.schema.json` (NEW JSON Schema)
- `src/shared/schemas/shot_material_bindings.py` (NEW Pydantic)
- `src/shared/types/shot_material_bindings.ts` (NEW TS)
- `schemas/shot_material_bindings.schema.json` (NEW JSON Schema)
- `src/shared/schemas/artifact_registry.py` (MODIFY 追加 2 条 P7A 条目)
- `tests/unit/contracts/test_material_manifest_schema.py` (NEW)

## Forbidden Files
- `src/backend/agents/**` (P7A Agent 实现由 C-021 承担)
- `src/backend/services/**`
- `src/backend/api/**`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1：两份 JSON Schema 校验合法/非法 payload，覆盖：material_id / shot_id 格式、material_type 枚举（chart/fact/news/figure/icon/image/video/quote）、required 枚举、source.kind 枚举、verification_status 枚举、phase 必为 "7A"
- [ ] AC-2：Pydantic + TS 镜像，字段名/必填一致
- [ ] AC-3：跨产物一致性测试：`bindings.required_materials` + `bindings.optional_materials` 中所有 material_id 必须能在 `material_manifest.materials[].material_id` 中找到（构造负样例必失败）
- [ ] AC-4：artifact registry 两条新条目（phase_7a/material_manifest.json, phase_7a/shot_material_bindings.json）落入 SPEC-0A.1
- [ ] AC-5：`verification_status` 状态机断言（pending → verified | rejected | missing），不允许从 verified 直接回 pending（除非通过 supplement 流程，需在 schema 注释明确）

## Verification Commands
```bash
pytest tests/unit/contracts/test_material_manifest_schema.py -v
mypy src/shared/schemas/material_manifest.py src/shared/schemas/shot_material_bindings.py --strict --explicit-package-bases
npx tsc --noEmit src/shared/types/material_manifest.ts src/shared/types/shot_material_bindings.ts
# 注：AC-2 跨语言一致性由上面 pytest 中的 test_pydantic_ts_alignment_{manifest,bindings} 覆盖
# 原先第 4 条 `python scripts/contracts/check_schema_alignment.py` 依赖 scripts/** (SPEC-B 领地且与 Allowed Files 冲突)，且系统仅有 `python3` shim，已删除（与 SPEC-A-013/A-014 相同处理）
# mypy 的 `--explicit-package-bases` 用于避免 `src.shared.schemas.*` 与裸模块名双重发现 ("Source file found twice")
# §Test Mapping 从占位 `test_spec_a_015.py` 翻到 `test_material_manifest_schema.py`（该文件在 §Allowed Files 内，承载 AC 本体 18 条测试）；历史占位 stub `test_spec_a_015.py` 在 Allowed Files 外，保留不动，harness-cleanup 统一清理
```

## Completion Definition
两份 schema 三态就位 + artifact registry 两条新条目 + 全部 5 条 AC 测试 PASS + 跨产物 material_id 一致性正负例覆盖 + verification_status 状态机文档化。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/contracts/test_material_manifest_schema.py | TestAC1JsonSchemaPayloads::test_manifest_valid / test_manifest_invalid_material_type / test_manifest_invalid_material_id_pattern / test_manifest_invalid_shot_id_pattern / test_manifest_invalid_required_enum / test_manifest_invalid_source_kind / test_manifest_invalid_verification_status / test_phase_must_be_7a / test_bindings_valid / test_bindings_invalid_shot_id / test_bindings_invalid_material_id_pattern |
| AC-2 | tests/unit/contracts/test_material_manifest_schema.py | TestAC2PydanticTsAlignment::test_pydantic_ts_alignment_manifest / test_pydantic_ts_alignment_bindings |
| AC-3 | tests/unit/contracts/test_material_manifest_schema.py | TestAC3CrossArtifactConsistency::test_bindings_material_id_must_exist_in_manifest |
| AC-4 | tests/unit/contracts/test_material_manifest_schema.py | TestAC4RegistryEntries::test_registry_contains_two_p7a_entries |
| AC-5 | tests/unit/contracts/test_material_manifest_schema.py | TestAC5VerificationStatusTransitions::test_verification_status_transitions |

## §23.9 验收门禁映射
- 第 9 行：MaterialReadinessCheck 阻断 P8（本任务承担 schema 数据基础；执行逻辑由 C-022 承担）
