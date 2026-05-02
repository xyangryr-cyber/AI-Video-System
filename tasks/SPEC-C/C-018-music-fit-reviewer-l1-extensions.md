# [SPEC-C-018] MusicFitReviewer 升级 — 三项 L1 程序化检查

## Metadata
- **task_id**: SPEC-C-018
- **spec_ref**: `docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md` §C-AUDP7A-3
- **delta_id**: TECH-DELTA-02
- **depends_on**: [SPEC-C-017]
- **priority**: P0
- **estimated_complexity**: M

## Scope
在 v3.15 SPEC-9.5.2 `MusicFitReviewer` 类基础上**追加**（不重写）3 项 L1 检查：full_track_harmony / abrupt_transition_detection / speech_intelligibility_score。聚合规则：v3.15 4 项 + 本版 3 项任一 FAIL → 整体 FAIL；report 含每项明细。

## Allowed Files
- `src/backend/reviewers/music_fit_reviewer.py` (MODIFY 追加 3 个方法 + 修改 review() 聚合)
- `src/backend/reviewers/audio_analysis/` (NEW 目录；frequency_correlation.py / envelope_diff.py / lufs_snr.py)
- `tests/unit/reviewers/test_music_fit_reviewer_v317.py` (NEW；本版 3 项独立单测)
- `tests/integration/reviewers/test_music_fit_aggregate.py` (NEW；4+3 聚合 + 回归 v3.15)
- `tests/fixtures/audio/music_fit_v317/` (NEW 夹具：高 BGM / 突变 BGM / 正常 BGM 三组)

## Forbidden Files
- `src/shared/**`
- `src/backend/services/**`
- `src/backend/agents/**`
- `src/frontend/**`
- v3.15 既有 4 项方法签名 / 阈值（禁止重写）

## Acceptance Criteria
- [ ] AC-1：`check_full_track_harmony()`：使用 pyloudnorm + 频谱相关性，spectral_correlation < 0.4 → FAIL；提供 PASS / FAIL 边界两例单测
- [ ] AC-2：`check_abrupt_transition()`：情绪转折点前后 2s 包络比对，rms_jump > 6dB 或 spectral_centroid_jump > 30% → FAIL；PASS / FAIL 单测
- [ ] AC-3：`check_speech_intelligibility()`：pyloudnorm LUFS 分窗，语音窗口 SNR < (narration_lufs - 6dB) → FAIL；PASS / FAIL 单测
- [ ] AC-4：聚合测试：v3.15 4 项 PASS + 本版 1 项 FAIL → 整体 FAIL；4 项 + 3 项全 PASS → PASS
- [ ] AC-5：构造高 BGM 夹具（speech_intelligibility 必 FAIL）→ 期望 FAIL；构造突变 BGM（abrupt_transition FAIL）→ 期望 FAIL
- [ ] AC-6：v3.15 既有 4 项测试套件回归全 PASS（不破坏既有契约）
- [ ] AC-7：report 结构：含 7 项各自 verdict + reason + 关键指标值（spectral_correlation / rms_jump / snr_db）

## Verification Commands
```bash
pytest tests/unit/backend-core/test_spec_c_018.py -v
# v3.15 既有测试回归
mypy src/backend/reviewers/music_fit_reviewer.py --strict
```

## Completion Definition
3 个新方法 + 聚合修改 + 全部 7 条 AC PASS + 三组夹具就位 + v3.15 既有 4 项测试零回归。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/backend-core/test_spec_c_018.py | test_full_track_harmony_pass / test_full_track_harmony_fail |
| AC-2 | tests/unit/backend-core/test_spec_c_018.py | test_abrupt_transition_pass / test_abrupt_transition_fail |
| AC-3 | tests/unit/backend-core/test_spec_c_018.py | test_speech_intelligibility_pass / test_speech_intelligibility_fail |
| AC-4 | tests/unit/backend-core/test_spec_c_018.py | test_aggregate_v315_pass_v317_fail / test_aggregate_all_pass |
| AC-5 | tests/unit/backend-core/test_spec_c_018.py | test_high_bgm_fixture_fails / test_abrupt_bgm_fixture_fails |
| AC-6 | tests/unit/backend-core/test_spec_c_018.py | test_v315_existing_checks_no_regression |
| AC-7 | tests/unit/backend-core/test_spec_c_018.py | test_report_structure_seven_checks |

## §23.9 验收门禁映射
- 第 4 行：MusicFitReviewer 三项新检查
