# [SPEC-B-010] 四类可观测证据与告警体系

## Metadata
- **task_id**: SPEC-B-010
- **spec_ref**: SPEC-13.4, SPEC-14.4
- **depends_on**: [SPEC-A-xxx] (SPEC-1A API 路由, SPEC-13B 统一日志格式), [SPEC-B-007], [SPEC-B-009]
- **priority**: P1
- **estimated_complexity**: M
- **bdd_tags**: [@observability]

## Scope
实现四类可观测证据的统一访问：状态(SQLite)、事件(events+WS)、LLM 审计(agent_call_log)、产物文件。实现告警检测逻辑：async_tasks 堆积（queued>10 且最老>30min）、Pre-flight 关键项 failed、leak_scan 命中、项目成本超 $15、degraded 项>2。每个告警有明确 owner，触发时写入日志（SPEC-A SPEC-13B 格式）。

## Allowed Files
- `src/backend/core/observability.py`
- `src/backend/core/alerts.py`
- `src/backend/api/routes/observability.py`
- `scripts/alert_check.py`
- `tests/unit/infra/test_observability.py`
- `tests/unit/infra/test_alerts.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: 四类可观测证据各有对应 API 且返回非空
- [ ] AC-2: phases 当前阶段与最新 `phase.entered` 事件一致
- [ ] AC-3: async_tasks 堆积告警：queued>10 且最老>30min 时输出 WARN
- [ ] AC-4: 每个告警信号有明确 owner 字段
- [ ] AC-5: 告警触发时日志格式符合 SPEC-A SPEC-13B 统一日志格式
- [ ] AC-6: 默认告警阈值：队列深度 WARN=10/CRITICAL=20，成本 WARN=$15

## Verification Commands
```bash
pytest tests/unit/infra/test_spec_b_010.py -v
```

## Completion Definition
四类可观测证据可通过 API 访问，告警检测逻辑正确触发并写入结构化日志。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/infra/test_spec_b_010.py | test_four_evidence_types_non_empty |
| AC-2 | tests/unit/infra/test_spec_b_010.py | test_phase_consistency_with_events |
| AC-3 | tests/unit/infra/test_spec_b_010.py | test_queue_buildup_alert |
| AC-4 | tests/unit/infra/test_spec_b_010.py | test_alert_has_owner_field |
| AC-5 | tests/unit/infra/test_spec_b_010.py | test_alert_log_format_spec_13b |
| AC-6 | tests/unit/infra/test_spec_b_010.py | test_default_alert_thresholds |
