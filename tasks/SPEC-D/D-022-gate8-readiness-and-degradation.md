# [SPEC-D-022] Gate-P8 升级：material readiness 前置 + 降级二分

## Metadata
- **task_id**: SPEC-D-022
- **spec_ref**: `docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md` §D-AUDP7A-5
- **delta_id**: PRD-DELTA-08 / TECH-DELTA-07
- **depends_on**: [SPEC-A-018, SPEC-C-022, SPEC-D-021]
- **priority**: P0
- **estimated_complexity**: M
- **bdd_tags**: [@phase8]

## Scope
SPEC-9.8.3 Gate-P8 追加 MaterialReadinessCheck 前置 + 降级二分（render_failed 工程降级 / material_missing|unverified 事实阻塞 + 回跳 phase_7a）；SPEC-9.8.2 VisualReviewer 追加物料一致性 L1 检查；SPEC-9.8.4 失败恢复路径表追加 30% 阈值告警 + 自动回跳。

## Allowed Files
- `src/backend/gates/gate_p8.py` (MODIFY 追加前置 + 降级聚合)
- `src/backend/reviewers/visual_reviewer.py` (MODIFY 追加物料一致性 L1)
- `src/backend/recovery/p8_recovery_paths.py` (MODIFY 30% 告警 + 回跳)
- `tests/unit/gates/test_gate_p8_v317.py` (NEW)
- `tests/integration/gates/test_p8_degradation_split.py` (NEW)

## Forbidden Files
- `src/shared/**`
- `src/backend/services/material_readiness_check.py` (由 C-022 维护)
- `src/backend/agents/keyframe_render_agent.py` (由 F-014 维护)
- `src/frontend/**`
- v3.15 既有 Gate-P8 断言（不删不改）

## Acceptance Criteria
- [ ] AC-1：1 shot render_failed → 该 shot 替默认文字卡，Gate 仍 PASS（其他 shot 继续）
- [ ] AC-2：1 shot material_missing → Gate FAIL，触发回跳 phase_7a（FSM 边由 D-021 提供，本任务断言 trigger）
- [ ] AC-3：5 shot 中 2 个 render_failed → 比例 < 30%，Gate PASS；6 shot 中 2 个 render_failed → 比例 = 33% > 30%，Gate FAIL + P0 告警
- [ ] AC-4：物料一致性 L1：构造 chart_material 与渲染数据不一致（hash 校验失败）→ VisualReviewer FAIL
- [ ] AC-5：v3.15 既有 Gate-P8 断言全套回归 PASS（v3.16 D-BDD-1 跨阶段 Claim 阻断也保留）
- [ ] AC-6：MaterialReadinessCheck 前置在 Gate 入口第一步执行；不通过则不进入后续渲染检查
- [ ] AC-7：v3.16 D-BDD-1 + 本版 D-AUDP7A-5 双重断言联合 PASS 才 Gate PASS（构造一项 FAIL 必拦截）

## Verification Commands
```bash
pytest tests/unit/pipeline/test_spec_d_022.py -v
mypy src/backend/gates/gate_p8.py src/backend/reviewers/visual_reviewer.py --strict
```

## Completion Definition
前置 + 降级二分 + 30% 阈值告警 + 物料一致性 L1 + 全部 7 条 AC PASS + v3.15 + v3.16 零回归。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/pipeline/test_spec_d_022.py | test_render_failed_one_shot_fallback_text |
| AC-2 | tests/unit/pipeline/test_spec_d_022.py | test_material_missing_jumps_back_phase_7a |
| AC-3 | tests/unit/pipeline/test_spec_d_022.py | test_render_failed_ratio_below_threshold / test_render_failed_ratio_exceeds_threshold |
| AC-4 | tests/unit/pipeline/test_spec_d_022.py | test_visual_reviewer_chart_material_consistency |
| AC-5 | tests/unit/pipeline/test_spec_d_022.py | (existing v3.15 + v3.16 suites) |
| AC-6 | tests/unit/pipeline/test_spec_d_022.py | test_readiness_check_first_step |
| AC-7 | tests/unit/pipeline/test_spec_d_022.py | test_v316_and_v317_assertions_joint |

## §23.9 验收门禁映射
- 第 8 行 / 第 9 行的 Gate 入口
