# [SPEC-C-022] MaterialReadinessCheck + MaterialReadinessReviewer + WorkflowEngine P8 启动接入

## Metadata
- **task_id**: SPEC-C-022
- **spec_ref**: `docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md` §C-AUDP7A-7
- **delta_id**: TECH-DELTA-07
- **depends_on**: [SPEC-A-015, SPEC-A-018, SPEC-C-021]
- **priority**: P0
- **estimated_complexity**: M

## Scope
新增 `MaterialReadinessCheck`（P8 async 任务启动前第一步执行的程序化前置）+ `MaterialReadinessReviewer`（Gate 7A 入口）。WorkflowEngine 接入：P8 启动入口先调用 Check；不通过 → 不进入 P8，发布 `phase.shot_blocked` 事件 + 设置回跳 `phase_7a` 标志。

## Allowed Files
- `src/backend/services/material_readiness_check.py` (NEW)
- `src/backend/reviewers/material_readiness_reviewer.py` (NEW Gate 7A 入口)
- `src/backend/engine/p8_starter.py` (MODIFY 接入 Check)
- `src/backend/engine/event_publisher.py` (MODIFY 加 phase.shot_blocked 发布)
- `tests/unit/services/test_material_readiness_check.py` (NEW)
- `tests/unit/reviewers/test_material_readiness_reviewer.py` (NEW)
- `tests/integration/engine/test_p8_blocked_by_unverified.py` (NEW)

## Forbidden Files
- `src/shared/**`
- `src/backend/agents/**`
- `src/backend/api/**`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1：所有物料 verified → `MaterialReadinessCheck.check()` 返回 `{ok=True, blocked_shots=[]}`
- [ ] AC-2：1 个 hard required = unverified（status=pending/missing/rejected 任一）→ `ok=False`，blocked_shots 含该 shot 与 error_code（material_unverified 或 material_missing 视情况）
- [ ] AC-3：1 个 soft required = unverified → `ok=True`（不阻断），但日志含 WARN 级提示
- [ ] AC-4：集成测试：phase_7a 留 1 个 hard required = unverified → P8 启动 FAIL，phase 不推进，broadcast `phase.shot_blocked` 事件携带正确 shot_id + error_code + blocking_material_ids
- [ ] AC-5：`MaterialReadinessReviewer.review()` 与 `Check` 结论一致（同输入两者 verdict 必一致；ConsistencyError 测试）
- [ ] AC-6：bound required material count 与 manifest count 不一致 → ok=False，error_code=`material_missing`（绑定列表 ⊃ manifest 时）
- [ ] AC-7：Check 函数的执行时间 < 200ms（即使 100 个 shot，性能基准）

## Verification Commands
```bash
pytest tests/unit/backend-core/test_spec_c_022.py -v
mypy src/backend/services/material_readiness_check.py src/backend/reviewers/material_readiness_reviewer.py --strict
# 性能基准
```

## Completion Definition
Check 服务 + Reviewer + P8 starter 接入 + 事件发布 + 全部 7 条 AC PASS + 性能基准达标。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/backend-core/test_spec_c_022.py | test_all_verified_returns_ok |
| AC-2 | tests/unit/backend-core/test_spec_c_022.py | test_hard_unverified_blocks_with_error_code |
| AC-3 | tests/unit/backend-core/test_spec_c_022.py | test_soft_unverified_warns_not_blocks |
| AC-4 | tests/unit/backend-core/test_spec_c_022.py | test_p8_blocked_event_emitted_with_payload |
| AC-5 | tests/unit/backend-core/test_spec_c_022.py | test_reviewer_consistent_with_check |
| AC-6 | tests/unit/backend-core/test_spec_c_022.py | test_count_mismatch_yields_material_missing |
| AC-7 | tests/unit/backend-core/test_spec_c_022.py | test_check_perf_under_200ms |

## §23.9 验收门禁映射
- 第 9 行：MaterialReadinessCheck 阻断 P8
