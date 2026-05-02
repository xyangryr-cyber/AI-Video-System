# [SPEC-D-020] Gate-P6 升级：双层 + 加工分段 + 最终主文件

## Metadata
- **task_id**: SPEC-D-020
- **spec_ref**: `docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md` §D-AUDP7A-3
- **delta_id**: PRD-DELTA-04 / PRD-DELTA-05 / TECH-DELTA-03 / TECH-DELTA-04
- **depends_on**: [SPEC-C-019, SPEC-C-020, SPEC-D-019]
- **priority**: P0
- **estimated_complexity**: L

## Scope
SPEC-9.6.3 Gate-P6 追加 10 项 L1 检查：sfx_layout_plan 存在 / user_confirmed_layout / sfx_mix_segments 完整 / 每段 mp3 存在 / 段 checksum / 最终主文件就绪 / 最终主文件可播放 / source_ref 链回 base_master / master_audio_ref 切换 / Layout+Mix Reviewer 双 PASS。

## Allowed Files
- `src/backend/gates/gate_p6.py` (MODIFY 追加 10 检查 + 聚合)
- `src/backend/gates/audio_master_checks.py` (复用)
- `src/backend/recovery/p6_recovery_paths.py` (MODIFY)
- `tests/unit/gates/test_gate_p6_v317.py` (NEW)
- `tests/integration/gates/test_gate_p6_full_chain.py` (NEW)

## Forbidden Files
- `src/shared/**`
- `src/backend/services/**` (由 C-019 维护)
- `src/backend/reviewers/sfx_*.py` (由 C-020 维护)
- `src/frontend/**`
- v3.15 既有 Gate-P6 断言（不删不改）

## Acceptance Criteria
- [ ] AC-1：10 个新检查独立单测，各 PASS / FAIL 一例
- [ ] AC-2：未确认 layout（user_confirmed_layout=false 或 task_ledger 无 confirm_sfx_layout）→ FAIL
- [ ] AC-3：单 segment checksum 不一致 → FAIL（其他段 OK 不绕过）
- [ ] AC-4：source_ref 链不一致（final_audio_master.source_ref.checksum != base_master.checksum）→ FAIL
- [ ] AC-5：SfxLayoutReviewer FAIL 或 SfxMixReviewer FAIL → Gate FAIL（任一 FAIL 拦截）
- [ ] AC-6：v3.15 Gate-P6 既有断言全套回归 PASS

## Verification Commands
```bash
pytest tests/unit/pipeline/test_spec_d_020.py -v
mypy src/backend/gates/gate_p6.py --strict
```

## Completion Definition
10 项检查 + 聚合 + 全部 6 条 AC PASS + v3.15 零回归。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/pipeline/test_spec_d_020.py | test_layout_plan_exists / test_user_confirmed_layout / test_mix_segments_complete / test_each_segment_mp3_exists / test_segment_checksum / test_final_master_exists / test_final_master_playable / test_source_ref_checksum / test_master_audio_ref_switched / test_layout_and_mix_reviewer_pass |
| AC-2 | tests/unit/pipeline/test_spec_d_020.py | test_unconfirmed_layout_fails |
| AC-3 | tests/unit/pipeline/test_spec_d_020.py | test_single_segment_checksum_mismatch_fails |
| AC-4 | tests/unit/pipeline/test_spec_d_020.py | test_source_ref_chain_mismatch_fails |
| AC-5 | tests/unit/pipeline/test_spec_d_020.py | test_layout_or_mix_reviewer_fail_blocks |
| AC-6 | tests/unit/pipeline/test_spec_d_020.py | (existing v3.15 suite) |

## §23.9 验收门禁映射
- 第 5 行 / 第 6 行的 Gate 入口
