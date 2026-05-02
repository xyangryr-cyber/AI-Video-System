# [SPEC-A-013] MasterAudioArtifact schema + ProjectState.master_audio_ref + artifact registry 扩展

## Metadata
- **task_id**: SPEC-A-013
- **spec_ref**: `docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md` §A-AUDP7A-1
- **delta_id**: PRD-DELTA-01 / PRD-DELTA-03 / PRD-DELTA-05 / TECH-DELTA-01
- **depends_on**: []
- **priority**: P0
- **estimated_complexity**: M

## Scope
新增 `MasterAudioArtifact`（按 `kind` 判别的三种主音频文件统一 schema：narration_master / bgm_mix_master / final_audio_master），扩展 `ProjectState` 增加 `master_audio_ref` 可选字段，并在 SPEC-0A.1 artifact registry 追加三条主文件条目。给出 JSON Schema、Pydantic 与 TypeScript 三方契约 + checksum 链验证规则。

## Allowed Files
- `src/shared/schemas/audio_master.py` (NEW Pydantic)
- `src/shared/types/audio_master.ts` (NEW TS)
- `schemas/audio_master.schema.json` (NEW JSON Schema)
- `src/shared/schemas/project_state.py` (MODIFY 追加 master_audio_ref)
- `src/shared/types/project_state.ts` (MODIFY 追加 master_audio_ref)
- `src/shared/schemas/artifact_registry.py` (MODIFY 追加 3 条主音频条目)
- `tests/unit/contracts/test_audio_master_schema.py` (NEW)

## Forbidden Files
- `src/backend/services/**`
- `src/backend/agents/**`
- `src/backend/api/**`
- `src/frontend/**`
- 任何 SPEC-B/C/D/E/F 范围内文件

## Acceptance Criteria
- [ ] AC-1：`audio_master.schema.json` 校验三种 kind 合法/非法 payload；非法案例覆盖（缺 source_ref 时 bgm_mix_master/final_audio_master 必失败 / narration_master 含 source_ref 必失败）
- [ ] AC-2：Pydantic `MasterAudioArtifact`（discriminated union by `kind`）+ TS `MasterAudioArtifact` 字段一一对应；round-trip 序列化无字段丢失
- [ ] AC-3：`ProjectState.master_audio_ref` 进入 SPEC-0A.3 / Pydantic / TS（可选字段，不破坏既有调用）
- [ ] AC-4：artifact registry 三条新条目（phase_4/narration_master.{mp3,json}, phase_5/bgm_mix_master.{mp3,json}, phase_6/final_audio_with_bgm_sfx.{mp3,json}）落入 SPEC-0A.1 表，含 producer/consumer/validation 列
- [ ] AC-5：单测断言 checksum 链：`bgm_mix_master.source_ref.checksum == narration_master.checksum`；`final_audio_master.source_ref.checksum == bgm_mix_master.checksum`
- [ ] AC-6：跨语言一致性测试：JSON Schema / Pydantic / TS interface 三方字段名与必填标记一致（snapshot diff = 0）

## Verification Commands
```bash
pytest tests/unit/contracts/test_spec_a_013.py -v
mypy src/shared/schemas/audio_master.py --strict
npx tsc --noEmit src/shared/types/audio_master.ts
# 注：跨语言一致性（AC-6）由上面 pytest 中的 test_cross_language_field_alignment 覆盖
# 原先第 4 条 `scripts/contracts/check_schema_alignment.py` 依赖 SPEC-B 脚本，与 Forbidden Files 冲突，已删除
```

## Completion Definition
三方 schema 文件就位 + Pydantic discriminated union 工作正常 + ProjectState 扩展字段 + artifact registry 三新条目 + 全部 6 条 AC 测试 PASS + checksum 链单测覆盖 PASS / FAIL 边界。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/contracts/test_spec_a_013.py | test_narration_master_valid / test_bgm_mix_master_requires_source_ref / test_narration_master_rejects_source_ref / test_invalid_kind_rejected |
| AC-2 | tests/unit/contracts/test_spec_a_013.py | test_pydantic_round_trip_three_kinds / test_ts_pydantic_field_parity |
| AC-3 | tests/unit/contracts/test_spec_a_013.py | test_project_state_master_audio_ref_optional / test_project_state_master_audio_ref_valid_payload |
| AC-4 | tests/unit/contracts/test_spec_a_013.py | test_registry_contains_three_master_audio_entries |
| AC-5 | tests/unit/contracts/test_spec_a_013.py | test_checksum_chain_bgm_to_narration / test_checksum_chain_final_to_bgm |
| AC-6 | tests/unit/contracts/test_spec_a_013.py | test_cross_language_field_alignment |

## §23.9 验收门禁映射
- 第 1 行：MasterAudioArtifact schema + `master_audio_ref` 迁移（本任务承担 schema 部分；migration 由 B-013 承担）

## Notes
- 仅 schema 与契约层；任何业务逻辑（拼接、校验、读写）禁止在此 task 实现，由 C-016 / D-018 承担。
- `phase_4`/`phase_5`/`phase_6` 路径前缀模式与 B-014 存储目录规范保持一致。
