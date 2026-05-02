# [SPEC-D-019] Gate-P5 升级：混音预览 + 主文件 + 基线切换

## Metadata
- **task_id**: SPEC-D-019
- **spec_ref**: `docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md` §D-AUDP7A-2
- **delta_id**: PRD-DELTA-02 / PRD-DELTA-03 / TECH-DELTA-02
- **depends_on**: [SPEC-C-017, SPEC-C-018, SPEC-D-018]
- **priority**: P0
- **estimated_complexity**: M

## Scope
SPEC-9.5.3 Gate-P5 追加 6 项 L1 检查（候选混音预览 / 用户选定 / 主文件就绪 / 主文件可播放 / source_ref 链回 narration / master_audio_ref 切换）+ MusicFitReviewer 含 v3.17 三项联合 PASS + no_bgm 跳过路径处理。

## Allowed Files
- `src/backend/gates/gate_p5.py` (MODIFY 追加 6 检查 + no_bgm 路径)
- `src/backend/gates/audio_master_checks.py` (复用 D-018 工具；本任务可少量扩展)
- `src/backend/recovery/p5_recovery_paths.py` (MODIFY)
- `tests/unit/gates/test_gate_p5_v317.py` (NEW)
- `tests/integration/gates/test_gate_p5_no_bgm_path.py` (NEW)

## Forbidden Files
- `src/shared/**`
- `src/backend/services/**` (由 C-017 维护)
- `src/backend/reviewers/music_fit_reviewer.py` (由 C-018 维护)
- `src/frontend/**`
- v3.15 既有 Gate-P5 断言（不删不改）

## Acceptance Criteria
- [ ] AC-1：6 个新检查独立单测：候选含 preview_url 指向混音预览文件 / task_ledger 含 select_bgm 操作 / phase_5/bgm_mix_master.{mp3,json} 存在 / ffprobe 可播放 / source_ref.checksum == narration_master.checksum / master_audio_ref.kind == bgm_mix_master
- [ ] AC-2：跳过 P5 路径单测（用户选 no_bgm）：task_ledger 含 select_no_bgm；master_audio_ref 回退 narration_master；Gate PASS 条件相应满足（6 项中部分豁免）
- [ ] AC-3：source_ref.checksum 与 narration_master.checksum 不一致 → FAIL（构造负样例）
- [ ] AC-4：v3.15 + v3.17 MusicFitReviewer 联合 PASS 才整体 PASS（v3.15 4 项 PASS + v3.17 3 项 PASS）；任一 FAIL → Gate FAIL
- [ ] AC-5：v3.15 Gate-P5 既有断言全套回归 PASS

## Verification Commands
```bash
pytest tests/unit/pipeline/test_spec_d_019.py -v
mypy src/backend/gates/gate_p5.py --strict
```

## Completion Definition
6 项检查 + no_bgm 路径 + MusicFit 联合 + 全部 5 条 AC PASS + v3.15 零回归。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/pipeline/test_spec_d_019.py | test_candidate_preview_url / test_select_bgm_in_ledger / test_master_exists / test_master_playable / test_source_ref_checksum / test_master_audio_ref_switched |
| AC-2 | tests/unit/pipeline/test_spec_d_019.py | test_no_bgm_falls_back_to_narration |
| AC-3 | tests/unit/pipeline/test_spec_d_019.py | test_source_ref_mismatch_fails |
| AC-4 | tests/unit/pipeline/test_spec_d_019.py | test_music_fit_v315_v317_joint_pass |
| AC-5 | tests/unit/pipeline/test_spec_d_019.py | (existing v3.15 suite) |

## §23.9 验收门禁映射
- 第 3 行 / 第 4 行的 Gate 入口
