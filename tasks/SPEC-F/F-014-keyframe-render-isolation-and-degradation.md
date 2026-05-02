# [SPEC-F-014] KeyframeRenderAgent 出站隔离 + 降级二分（render_failed / material_*）

## Metadata
- **task_id**: SPEC-F-014
- **spec_ref**: `docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md` §F-AUDP7A-2
- **delta_id**: PRD-DELTA-08 / TECH-DELTA-07
- **depends_on**: [SPEC-A-018, SPEC-B-016, SPEC-D-022]
- **priority**: P0
- **estimated_complexity**: M

## Scope
SPEC-19 KeyframeRenderAgent 实现层接入：出站约束（引用 B-016 outbound_whitelist）+ prompt 硬约束（禁止生成外部 URL，必须来自 phase_7a/）+ 降级二分（render_failed 工程降级为默认文字卡 / material_missing|unverified 上报阻断）+ 每条渲染结果带 error_code 字段（null | 三种之一）。SPEC-23 默认文字卡渲染基准 < 2s。

## Allowed Files
- `src/backend/agents/keyframe_render_agent.py` (MODIFY 接入降级二分 + 出站约束)
- `src/backend/render/default_text_card.py` (NEW；fallback 渲染)
- `src/backend/render/render_result.py` (MODIFY 加 error_code 字段)
- `config/prompts/keyframe_render_agent.md` (MODIFY 加硬约束 prompt)
- `tests/unit/agents/test_keyframe_render_agent_v317.py` (NEW)
- `tests/integration/agents/test_keyframe_degradation.py` (NEW)
- `tests/perf/test_default_text_card_perf.py` (NEW)

## Forbidden Files
- `src/shared/**`
- `src/backend/infra/outbound_gateway.py` (由 B-016 维护)
- `src/backend/services/material_readiness_check.py` (由 C-022 维护)
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1：mock 渲染异常（Remotion 报错）→ render_result 含 `error_code='render_failed'` + 默认文字卡产物路径
- [ ] AC-2：构造物料缺失场景（material 文件不存在）→ render_result.error_code='material_missing'，无产物
- [ ] AC-3：构造物料未验证（status != verified，理论上由 ReadinessCheck 拦截，此处为防御性）→ render_result.error_code='material_unverified'
- [ ] AC-4：调用非白名单 host → 网关抛 `OutboundBlockedException`，KeyframeRenderAgent 捕获并上报 `error_code='render_failed'`
- [ ] AC-5：默认文字卡渲染基准：单帧 < 2s（使用 standard fixture，CI benchmark）
- [ ] AC-6：每条 render_result 都携带 `error_code` 字段（成功 = null）；缺字段抛 `MalformedRenderResultError`
- [ ] AC-7：prompt 硬约束生效：mock LLM 返回外部 URL → 出站层硬阻断，agent 不发起请求

## Verification Commands
```bash
pytest tests/unit/media-render/test_spec_f_014.py -v
mypy src/backend/agents/keyframe_render_agent.py src/backend/render/default_text_card.py src/backend/render/render_result.py --strict
```

## Completion Definition
Agent 改造 + 文字卡 + render_result 字段 + prompt + 全部 7 条 AC PASS + 性能基准达标。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/media-render/test_spec_f_014.py | test_render_exception_yields_text_card |
| AC-2 | tests/unit/media-render/test_spec_f_014.py | test_material_missing_no_artifact |
| AC-3 | tests/unit/media-render/test_spec_f_014.py | test_material_unverified_defensive_path |
| AC-4 | tests/unit/media-render/test_spec_f_014.py | test_outbound_blocked_reported_as_render_failed |
| AC-5 | tests/unit/media-render/test_spec_f_014.py | test_text_card_under_2s |
| AC-6 | tests/unit/media-render/test_spec_f_014.py | test_render_result_error_code_required |
| AC-7 | tests/unit/media-render/test_spec_f_014.py | test_prompt_hard_constraint_outbound_blocked |

## §23.9 验收门禁映射
- 第 9 行：MaterialReadinessCheck 阻断 P8（渲染侧二分实现）
