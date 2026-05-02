# [SPEC-C-019] SfxSegmentMixService + FinalAudioAssembler（P6 双层 + 最终主音频）

## Metadata
- **task_id**: SPEC-C-019
- **spec_ref**: `docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md` §C-AUDP7A-4
- **delta_id**: TECH-DELTA-03
- **depends_on**: [SPEC-A-013, SPEC-A-014, SPEC-C-016, SPEC-C-017]
- **priority**: P0
- **estimated_complexity**: L

## Scope
新增 `SfxSegmentMixService`（基于 base_master 按段叠加 trigger，输出编号分段 + 写 sfx_mix_segments.json）+ `FinalAudioAssembler`（串联所有 segment → final_audio_with_bgm_sfx.mp3，符合 A-013 audio_master final_audio_master schema，更新 master_audio_ref）。强制 user_confirmed_layout 约束。

## Allowed Files
- `src/backend/services/sfx_segment_mix_service.py` (NEW)
- `src/backend/services/final_audio_assembler.py` (NEW)
- `src/backend/services/sfx_layout_planner.py` (NEW；编排 LLM Agent，仅约束输出 schema = sfx_layout_plan.json)
- `src/backend/repositories/project_state_repo.py` (MODIFY 复用 master_audio_ref 写入)
- `src/backend/exceptions/sfx_exceptions.py` (NEW LayoutNotConfirmedError)
- `tests/unit/services/test_sfx_segment_mix_service.py` (NEW)
- `tests/unit/services/test_final_audio_assembler.py` (NEW)
- `tests/integration/services/test_p6_pipeline_e2e.py` (NEW)
- `tests/fixtures/audio/p6/` (NEW 夹具)

## Forbidden Files
- `src/shared/**`
- `src/backend/agents/**`
- `src/backend/reviewers/sfx_*.py` (Reviewer 拆分由 C-020 承担)
- `src/backend/api/**`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1：`mix_segment()` 单测：固定 base_master + 1 trigger → 输出 PCM 在 trigger 时间窗有 SFX 能量（pyloudnorm RMS 验证）
- [ ] AC-2：`assemble()` 单测：N 段拼接后总时长 = ∑segments（±50ms 容差）；checksum 链 `final_audio_master.source_ref.checksum == base_master.checksum`
- [ ] AC-3：未确认 layout（`user_confirmed_layout=false`）调用 `assemble()` → 抛 `LayoutNotConfirmedError`，不写产物
- [ ] AC-4：sfx_mix_segments.json 与文件系统一致：每个 segment.file_path 文件存在；checksum 与 schema 中 checksum 一致
- [ ] AC-5：增量重做测试：单 segment 重 mix（同 trigger 列表）不改变其他 segment 的 checksum
- [ ] AC-6：FinalAudioAssembler 完成后 `master_audio_ref.kind=final_audio_master` + `based_on_phase=6`（DB 验证）
- [ ] AC-7：base_master 必须为 bgm_mix_master 或 narration_master（no_bgm 路径回退）；其他 kind 调用 `mix_segment()` 抛 `InvalidBaseMasterError`

## Verification Commands
```bash
pytest tests/unit/backend-core/test_spec_c_019.py -v
mypy src/backend/services/sfx_segment_mix_service.py src/backend/services/final_audio_assembler.py --strict
```

## Completion Definition
三个服务类 + 异常类 + 全部 7 条 AC PASS + e2e 覆盖正常路径 + LayoutNotConfirmed 拦截 + 增量重 mix 隔离 + base_master 校验。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/backend-core/test_spec_c_019.py | test_trigger_energy_in_window |
| AC-2 | tests/unit/backend-core/test_spec_c_019.py | test_assemble_total_duration / test_checksum_chain_to_base |
| AC-3 | tests/unit/backend-core/test_spec_c_019.py | test_layout_not_confirmed_raises |
| AC-4 | tests/unit/backend-core/test_spec_c_019.py | test_sfx_mix_segments_json_consistent_with_fs |
| AC-5 | tests/unit/backend-core/test_spec_c_019.py | test_single_segment_remix_isolation |
| AC-6 | tests/unit/backend-core/test_spec_c_019.py | test_master_audio_ref_final_kind |
| AC-7 | tests/unit/backend-core/test_spec_c_019.py | test_invalid_base_master_kind_raises |

## §23.9 验收门禁映射
- 第 5 行：sfx_layout_plan + sfx_mix_segments 双产物（与 A-014 协同；Gate 校验由 D-020 承担）
