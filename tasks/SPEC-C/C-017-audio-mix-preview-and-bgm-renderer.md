# [SPEC-C-017] AudioMixPreviewService + BgmMixRenderer（P5 混音预览 + 主混音渲染）

## Metadata
- **task_id**: SPEC-C-017
- **spec_ref**: `docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md` §C-AUDP7A-2
- **delta_id**: TECH-DELTA-02
- **depends_on**: [SPEC-A-013, SPEC-C-016, SPEC-B-014]
- **priority**: P0
- **estimated_complexity**: M

## Scope
新增 `AudioMixPreviewService`（候选 BGM × narration master → 混音预览文件，不更新 master_audio_ref）+ `BgmMixRenderer`（用户选定后产出 bgm_mix_master 主文件并切换 master_audio_ref）。候选卡片 preview_url 字段语义切换为混音预览。

## Allowed Files
- `src/backend/services/audio_mix_preview_service.py` (NEW)
- `src/backend/services/bgm_mix_renderer.py` (NEW)
- `src/backend/services/audio_envelope.py` (NEW or MODIFY；EnvelopeSpec 工具)
- `src/backend/repositories/project_state_repo.py` (MODIFY 复用 C-016 master_audio_ref 写入)
- `src/shared/schemas/bgm_candidate.py` (MODIFY 候选卡片 schema：preview_url + raw_bgm_url 双字段)
- `src/shared/types/bgm_candidate.ts` (MODIFY 同步)
- `tests/unit/services/test_audio_mix_preview_service.py` (NEW)
- `tests/unit/services/test_bgm_mix_renderer.py` (NEW)
- `tests/integration/services/test_p5_mix_e2e.py` (NEW)
- `tests/fixtures/audio/p5_mix/` (NEW 夹具)

## Forbidden Files
- `src/backend/agents/**`
- `src/backend/api/**`
- `src/backend/reviewers/music_fit_reviewer.py` (升级由 C-018 承担)
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1：`AudioMixPreviewService.render_preview()` 固定 narration + 固定 BGM + 固定 envelope → 输出 PCM 一致（确定性，hash 相同）
- [ ] AC-2：`BgmMixRenderer.render_master()` 输出 `bgm_mix_master.json` 中 `source_ref.checksum == narration_master.checksum`
- [ ] AC-3：`render_preview()` 不更新 `master_audio_ref`；`render_master()` 必须更新 `master_audio_ref`（DB query 验证）
- [ ] AC-4：ffprobe 校验 preview / master 文件可播放、采样率/通道数与 narration 一致
- [ ] AC-5：候选卡片 schema 测试：`preview_url`（混音）与 `raw_bgm_url`（原 BGM 试听）同时存在；既有调用方传入仅 `bgm_url` 单字段需向后兼容（标 deprecated 但不报错）
- [ ] AC-6：缺 narration_master 调用 `render_preview()` → 抛 `MasterAudioNotReadyError`

## Verification Commands
```bash
pytest tests/unit/backend-core/test_spec_c_017.py -v
mypy src/backend/services/audio_mix_preview_service.py src/backend/services/bgm_mix_renderer.py --strict
ffprobe -v error -show_streams tests/fixtures/audio/p5_mix/expected_master.mp3
```

## Completion Definition
两个服务类 + envelope 工具 + 候选 schema 双字段 + 全部 6 条 AC 测试 PASS + e2e 覆盖确定性混音 / master 切换 / 异常路径三条。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/backend-core/test_spec_c_017.py | test_preview_deterministic_pcm |
| AC-2 | tests/unit/backend-core/test_spec_c_017.py | test_master_source_ref_checksum_matches_narration |
| AC-3 | tests/unit/backend-core/test_spec_c_017.py | test_preview_does_not_update_ref / test_master_updates_ref |
| AC-4 | tests/unit/backend-core/test_spec_c_017.py | test_ffprobe_preview_and_master |
| AC-5 | tests/unit/backend-core/test_spec_c_017.py | test_candidate_card_preview_and_raw_urls / test_legacy_bgm_url_compat |
| AC-6 | tests/unit/backend-core/test_spec_c_017.py | test_missing_narration_master_raises |

## §23.9 验收门禁映射
- 第 3 行：AudioMixPreviewService 输出可播放
