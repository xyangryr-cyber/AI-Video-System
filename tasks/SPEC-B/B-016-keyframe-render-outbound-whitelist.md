# [SPEC-B-016] KeyframeRenderAgent 出站网关白名单配置

## Metadata
- **task_id**: SPEC-B-016
- **spec_ref**: `docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md` §B-AUDP7A-4
- **delta_id**: TECH-DELTA-07
- **depends_on**: []
- **priority**: P0
- **estimated_complexity**: S

## Scope
在 SPEC-12 出站网关追加 KeyframeRenderAgent 的白名单配置（仅允许内部 CDN / DataService / 本地）+ 阻断异常类型 + SPEC-13.2 安全规则 + SPEC-14.4 P0 告警归属。

## Allowed Files
- `config/outbound_whitelist.yaml` (MODIFY 追加 KeyframeRenderAgent 段)
- `src/backend/infra/outbound_gateway.py` (MODIFY 加载 + 校验)
- `src/backend/infra/exceptions.py` (MODIFY 追加 OutboundBlockedException)
- `tests/unit/infra/test_outbound_whitelist_keyframe.py` (NEW)
- `tests/integration/infra/test_keyframe_outbound_blocked.py` (NEW)

## Forbidden Files
- `src/backend/agents/keyframe_render_agent.py` (Prompt 硬约束由 F-014 承担)
- `src/shared/**`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1：`config/outbound_whitelist.yaml` 含 `agent: KeyframeRenderAgent` 段，allowed_hosts 包含 cdn.internal.aivs / financial-data.internal / localhost；blocked_apis 列表包含 b_roll_search / news_search / "any LLM-generated URL fetch"
- [ ] AC-2：`OutboundBlockedException` 在 `src/backend/infra/exceptions.py` 定义，含 host / agent / reason 字段
- [ ] AC-3：单测：构造 KeyframeRenderAgent 调用 `cdn.internal.aivs/...` → 通过；调用 `cdn.external.com/...` → 抛 `OutboundBlockedException`
- [ ] AC-4：日志契约：阻断时输出 `level=ERROR, event=outbound.blocked, agent=KeyframeRenderAgent, host=..., reason=...`
- [ ] AC-5：SPEC-14.4 告警表追加 `OutboundBlockedException` → P0 → Owner=渲染团队 DRI（文档同步追加，本任务仅在测试中断言告警事件可被捕获）
- [ ] AC-6：v3.15 既有出站规则不破坏（其他 agent 出站不受影响，回归测试）

## Verification Commands
```bash
pytest tests/unit/infra/test_spec_b_016.py -v
# 配置 schema 校验
python scripts/infra/validate_outbound_config.py config/outbound_whitelist.yaml
```

## Completion Definition
配置 + 网关代码 + 异常类 + 全部 6 条 AC 测试 PASS + v3.15 既有出站规则零回归 + SPEC-14.4 告警归属文档同步 hint 记录。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/infra/test_spec_b_016.py | test_config_has_keyframe_section / test_allowed_hosts_present / test_blocked_apis_present |
| AC-2 | tests/unit/infra/test_spec_b_016.py | test_outbound_blocked_exception_class |
| AC-3 | tests/unit/infra/test_spec_b_016.py | test_internal_cdn_passes / test_external_host_blocked |
| AC-4 | tests/unit/infra/test_spec_b_016.py | test_log_event_on_block |
| AC-5 | tests/unit/infra/test_spec_b_016.py | test_alert_event_captured_p0 |
| AC-6 | tests/unit/infra/test_spec_b_016.py | test_other_agents_outbound_unchanged |

## §23.9 验收门禁映射
- 第 9 行：MaterialReadinessCheck 阻断 P8（本任务承担网关侧防御；ReadinessCheck 由 C-022 承担；渲染降级由 F-014 承担）
