# [SPEC-D-021] 新增 Gate-7A + FSM phase_7a 边 + 回跳边 P8→phase_7a

## Metadata
- **task_id**: SPEC-D-021
- **spec_ref**: `docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md` §D-AUDP7A-4
- **delta_id**: PRD-DELTA-06 / TECH-DELTA-05 / TECH-DELTA-07
- **depends_on**: [SPEC-A-017, SPEC-C-021, SPEC-C-022]
- **priority**: P0
- **estimated_complexity**: M

## Scope
SPEC-3.6 状态机转换矩阵追加 3 条新边（P7→phase_7a / phase_7a→P8 / P8→phase_7a 回跳）；新增 SPEC-9.7A.1 子阶段定义 + SPEC-9.7A.2 Gate-7A；同步更新 SPEC-9.13 ViewerExperienceReviewer 输入说明。

## Allowed Files
- `src/backend/engine/fsm.py` (MODIFY 追加 3 条边 + phase_7a 状态)
- `src/backend/engine/fsm_transitions.py` (MODIFY 转换矩阵)
- `src/backend/gates/gate_7a.py` (NEW；调用 MaterialReadinessReviewer)
- `tests/unit/engine/test_fsm_phase_7a_edges.py` (NEW)
- `tests/integration/engine/test_phase_7a_lifecycle.py` (NEW)

## Forbidden Files
- `src/shared/types/phase_enum.ts` (由 A-017 维护)
- `src/backend/services/material_readiness_check.py` (由 C-022 维护)
- `src/backend/agents/**`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1：FSM 测试：P7 PASS → 自动进入 phase_7a（触发 StoryboardAssetPlanner 调用 hook）
- [ ] AC-2：FSM 测试：phase_7a Gate-7A PASS → 进入 P8（project_state.phase = P8）
- [ ] AC-3：FSM 测试：P8 运行时 MaterialReadinessCheck FAIL（构造 unverified hard required）→ 回跳 phase_7a，broadcast `phase.shot_blocked` 事件
- [ ] AC-4：phases 表 phase_id 列允许 `phase_7a` 值（DB 约束验证；与 A-017 + B-013 协同）
- [ ] AC-5：SPEC-9.7A.1 / 9.7A.2 章节内容完整（无 TBD/占位符）；本任务通过文档 PR 落地两节
- [ ] AC-6：SPEC-9.13 ViewerExperienceReviewer 输入说明追加可选消费 phase_7a 物料
- [ ] AC-7：非法转换抛 `IllegalStateTransition`（如 P5 → phase_7a 直跳必拒）

## Verification Commands
```bash
pytest tests/unit/pipeline/test_spec_d_021.py -v
mypy src/backend/engine/fsm.py src/backend/engine/fsm_transitions.py src/backend/gates/gate_7a.py --strict
# DB 约束验证
sqlite3 data/db/test.sqlite3 "INSERT INTO phases (project_id, phase_id) VALUES ('proj_test', 'phase_7a');"
```

## Completion Definition
FSM 3 条边 + Gate-7A 入口 + 新章节文档 + 全部 7 条 AC PASS + DB 约束允许。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/pipeline/test_spec_d_021.py | test_p7_pass_enters_phase_7a |
| AC-2 | tests/unit/pipeline/test_spec_d_021.py | test_phase_7a_pass_enters_p8 |
| AC-3 | tests/unit/pipeline/test_spec_d_021.py | test_p8_unverified_jumps_back_phase_7a / test_shot_blocked_event_broadcast |
| AC-4 | tests/unit/pipeline/test_spec_d_021.py | test_phases_table_allows_phase_7a |
| AC-5 | tests/unit/pipeline/test_spec_d_021.py | test_spec_9_7a_doc_present_no_placeholders |
| AC-6 | tests/unit/pipeline/test_spec_d_021.py | test_viewer_experience_reviewer_phase_7a_input |
| AC-7 | tests/unit/pipeline/test_spec_d_021.py | test_illegal_p5_to_phase_7a_raises |

## §23.9 验收门禁映射
- 第 7 行：P7A FSM 态位
