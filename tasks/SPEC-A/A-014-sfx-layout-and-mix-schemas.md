# [SPEC-A-014] SfxLayoutPlan + SfxMixSegments schemas（P6 双层模型）

## Metadata
- **task_id**: SPEC-A-014
- **spec_ref**: `docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md` §A-AUDP7A-2
- **delta_id**: PRD-DELTA-04 / TECH-DELTA-03
- **depends_on**: [SPEC-A-013]
- **priority**: P0
- **estimated_complexity**: M

## Scope
新增两份 schema 拆分 P6 之前扁平的 SFX 触发列表为"全局规划层（sfx_layout_plan.json）"和"局部加工层（sfx_mix_segments.json）"，并在 SPEC-0A.1 artifact registry 追加两条新条目。

## Allowed Files
- `src/shared/schemas/sfx_layout_plan.py` (NEW Pydantic)
- `src/shared/types/sfx_layout_plan.ts` (NEW TS)
- `schemas/sfx_layout_plan.schema.json` (NEW JSON Schema)
- `src/shared/schemas/sfx_mix_segments.py` (NEW Pydantic)
- `src/shared/types/sfx_mix_segments.ts` (NEW TS)
- `schemas/sfx_mix_segments.schema.json` (NEW JSON Schema)
- `src/shared/schemas/artifact_registry.py` (MODIFY 追加 2 条 SFX 条目)
- `tests/unit/contracts/test_sfx_schemas.py` (NEW)

## Forbidden Files
- `src/backend/services/**`
- `src/backend/agents/**`
- `src/backend/api/**`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1：两份 JSON Schema 校验合法/非法 payload，覆盖：trigger_id 格式、keyword_span 长度、planned_time_sec ≥ 0、segment_id 格式、checksum sha256 格式
- [ ] AC-2：Pydantic + TS 镜像，字段名/必填一致（snapshot diff = 0）
- [ ] AC-3：单测断言 `sfx_mix_segments.base_master` 必须匹配 `^(phase_5/bgm_mix_master|phase_4/narration_master)\.mp3$`（异常 base 必拒）
- [ ] AC-4：artifact registry 两条新条目（phase_6/sfx_layout_plan.json, phase_6/sfx_mix_segments.json）落入 SPEC-0A.1
- [ ] AC-5：跨产物一致性测试：`applied_triggers` 中每个 trigger_id 必须能在对应 plan_version 的 `sfx_layout_plan.triggers[].trigger_id` 中找到（构造负样例必失败）

## Verification Commands
```bash
pytest tests/unit/contracts/test_sfx_schemas.py -v
mypy src/shared/schemas/sfx_layout_plan.py src/shared/schemas/sfx_mix_segments.py --strict --explicit-package-bases
npx tsc --noEmit src/shared/types/sfx_layout_plan.ts src/shared/types/sfx_mix_segments.ts
# 注：AC-2 跨语言一致性由上面 pytest 中的 test_pydantic_ts_alignment_{layout,mix} 覆盖
# 原先第 4 条 `python scripts/contracts/check_schema_alignment.py` 依赖 scripts/** (SPEC-B 领地且与 Allowed Files 冲突)，且系统仅有 `python3` shim，已删除（与 SPEC-A-013 相同处理）
# mypy 的 `--explicit-package-bases` 用于避免 `src.shared.schemas.*` 与裸模块名双重发现 ("Source file found twice")
```

## Completion Definition
两份 schema 文件就位（JSON / Pydantic / TS 三态）+ artifact registry 两条新条目 + 全部 5 条 AC 测试 PASS + 跨产物 trigger_id 一致性测试覆盖正负例。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/contracts/test_sfx_schemas.py | TestAC1JsonSchemaPayloads::test_layout_plan_valid / test_layout_plan_invalid_trigger_id / test_layout_plan_invalid_keyword_span_length / test_layout_plan_invalid_planned_time_sec_negative / test_mix_segments_valid / test_mix_segments_invalid_checksum / test_mix_segments_invalid_segment_id |
| AC-2 | tests/unit/contracts/test_sfx_schemas.py | TestAC2PydanticTsAlignment::test_pydantic_ts_alignment_layout / test_pydantic_ts_alignment_mix |
| AC-3 | tests/unit/contracts/test_sfx_schemas.py | TestAC3BaseMasterPattern::test_base_master_pattern_enforced |
| AC-4 | tests/unit/contracts/test_sfx_schemas.py | TestAC4RegistryEntries::test_registry_contains_two_sfx_entries |
| AC-5 | tests/unit/contracts/test_sfx_schemas.py | TestAC5CrossArtifactConsistency::test_applied_triggers_must_exist_in_plan |

## §23.9 验收门禁映射
- 第 5 行：sfx_layout_plan.json + sfx_mix_segments.json 双产物在 P6 DONE 时存在（本任务承担 schema 部分；产物生成由 C-019 承担；Gate 校验由 D-020 承担）
