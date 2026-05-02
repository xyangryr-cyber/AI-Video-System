# [SPEC-D-018] Gate-P4 升级：主文件完整性 + 拼接校验

## Metadata
- **task_id**: SPEC-D-018
- **spec_ref**: `docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md` §D-AUDP7A-1
- **delta_id**: PRD-DELTA-01 / TECH-DELTA-01
- **depends_on**: [SPEC-A-013, SPEC-C-016]
- **priority**: P0
- **estimated_complexity**: M

## Scope
在 v3.15 SPEC-9.4.3 Gate-P4 既有断言基础上**追加** 5 项 L1 检查：主文件存在 / 可播放 / 拼接完整性 / checksum 一致 / master_audio_ref 切换。SPEC-9.4.4 失败恢复路径表追加重跑/重试规则。

## Allowed Files
- `src/backend/gates/gate_p4.py` (MODIFY 追加 5 检查 + 聚合)
- `src/backend/gates/audio_master_checks.py` (NEW；3 项可复用 audio 检查工具：existence / playable / checksum)
- `src/backend/recovery/p4_recovery_paths.py` (MODIFY 追加 narration_master 重跑路径)
- `tests/unit/gates/test_gate_p4_v317.py` (NEW)
- `tests/integration/gates/test_gate_p4_recovery.py` (NEW)

## Forbidden Files
- `src/shared/**`
- `src/backend/services/narration_master_assembler.py` (由 C-016 维护)
- `src/backend/api/**`
- `src/frontend/**`
- v3.15 既有 Gate-P4 断言（不删不改）

## Acceptance Criteria
- [ ] AC-1：5 个新检查各有独立单测：master 文件存在（缺 → FAIL）/ ffprobe 可播放（duration ≤ 0 → FAIL）/ 拼接完整性 sum(seg.duration) ≈ master.duration_sec ±50ms / checksum 重算 ≠ json.checksum → FAIL / master_audio_ref.kind ≠ "narration_master" → FAIL
- [ ] AC-2：聚合测试：构造一个 segment 丢失场景 → 拼接完整性 FAIL → Gate FAIL；其他四项 PASS 不绕过
- [ ] AC-3：v3.15 Gate-P4 既有断言全套回归 PASS（不破坏）
- [ ] AC-4：失败恢复路径单测：拼接完整性 FAIL → 自动触发 NarrationMasterAssembler 重跑（不重 TTS）；master_audio_ref DB 写入失败 → 重试 ≤ 3 次
- [ ] AC-5：Gate 报告结构：含 5 项 v3.17 检查 + N 项 v3.15 检查的明细 verdict 与 reason

## Verification Commands
```bash
pytest tests/unit/pipeline/test_spec_d_018.py -v
# v3.15 回归
mypy src/backend/gates/gate_p4.py src/backend/gates/audio_master_checks.py --strict
```

## Completion Definition
5 项检查 + 聚合 + 恢复路径 + 全部 5 条 AC PASS + v3.15 零回归。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/pipeline/test_spec_d_018.py | test_master_exists / test_master_playable / test_concat_integrity / test_checksum_consistent / test_master_audio_ref_switched |
| AC-2 | tests/unit/pipeline/test_spec_d_018.py | test_missing_segment_fails_gate |
| AC-3 | tests/unit/pipeline/test_spec_d_018.py | (existing v3.15 suite) |
| AC-4 | tests/unit/pipeline/test_spec_d_018.py | test_concat_failure_triggers_assembler_rerun / test_master_audio_ref_db_retry |
| AC-5 | tests/unit/pipeline/test_spec_d_018.py | test_gate_report_structure |

## §23.9 验收门禁映射
- 第 2 行的 Gate 入口（NarrationMasterAssembler 拼接校验由 C-016 保障，本 Gate 卡断阶段交付）
