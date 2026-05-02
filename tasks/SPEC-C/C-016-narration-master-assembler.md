# [SPEC-C-016] NarrationMasterAssembler 服务（P4 主音频拼接）

## Metadata
- **task_id**: SPEC-C-016
- **spec_ref**: `docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md` §C-AUDP7A-1
- **delta_id**: TECH-DELTA-01
- **depends_on**: [SPEC-A-013, SPEC-B-013, SPEC-B-014]
- **priority**: P0
- **estimated_complexity**: M

## Scope
新增 `NarrationMasterAssembler` 服务：把 P4 TTS 段产物（timeline.json + seg_XX.mp3）按顺序无损拼接为 `phase_4/narration_master.{mp3,json}`，符合 A-013 audio_master schema，并在事务内更新 `project_state.master_audio_ref` + DB。

## Allowed Files
- `src/backend/services/narration_master_assembler.py` (NEW)
- `src/backend/services/audio_concat.py` (NEW or MODIFY；ffmpeg concat demuxer 封装)
- `src/backend/repositories/project_state_repo.py` (MODIFY 加 master_audio_ref 写入方法)
- `tests/unit/services/test_narration_master_assembler.py` (NEW)
- `tests/integration/services/test_narration_master_e2e.py` (NEW)
- `tests/fixtures/audio/narration_segments/` (NEW 测试夹具)

## Forbidden Files
- `src/shared/**`
- `src/backend/agents/**`
- `src/backend/api/**`
- `src/backend/workers/**`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1：拼接 3 段 narration → 输出 narration_master.mp3，解码后 PCM 与原 3 段拼接的 PCM diff = 0（无损）
- [ ] AC-2：构造一个 segment 文件缺失 → 抛 `MissingSegmentError`，不写 master 也不更新 master_audio_ref（事务性）
- [ ] AC-3：checksum 计算稳定：同输入两次拼接产生同 sha256
- [ ] AC-4：成功后 `project_state.master_audio_ref` 持久化（DB query 验证），字段值通过 A-013 schema 校验
- [ ] AC-5：拼接失败时不污染 master_audio_ref（事务回滚）+ 不留半成品 master 文件
- [ ] AC-6：narration_master.json 元数据正确：kind=narration_master / based_on_phase=4 / derived_from_segments=[seg_01,seg_02,seg_03] / total_duration_seconds 与 ffprobe 测得一致 / version=1（首次）/ 重跑 version 递增

## Verification Commands
```bash
pytest tests/unit/backend-core/test_spec_c_016.py -v
mypy src/backend/services/narration_master_assembler.py --strict
ffprobe -v error -show_format tests/fixtures/audio/narration_segments/expected_master.mp3
```

## Completion Definition
服务类 + audio_concat 工具 + repo 写入方法 + 全部 6 条 AC 测试 PASS + e2e 集成测试覆盖正常 + 失败回滚两条路径。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/backend-core/test_spec_c_016.py | test_lossless_concat_three_segments |
| AC-2 | tests/unit/backend-core/test_spec_c_016.py | test_missing_segment_raises_and_no_master |
| AC-3 | tests/unit/backend-core/test_spec_c_016.py | test_checksum_stable_across_runs |
| AC-4 | tests/unit/backend-core/test_spec_c_016.py | test_master_audio_ref_persisted |
| AC-5 | tests/unit/backend-core/test_spec_c_016.py | test_failed_assemble_does_not_pollute_state |
| AC-6 | tests/unit/backend-core/test_spec_c_016.py | test_metadata_fields / test_version_increments_on_rerun |

## §23.9 验收门禁映射
- 第 2 行：NarrationMasterAssembler 拼接校验
