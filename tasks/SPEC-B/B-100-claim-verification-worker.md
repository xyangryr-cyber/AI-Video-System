# [SPEC-B-100] claim_verification 队列 + 告警 + Dashboard 指标

## Metadata
- **task_id**: SPEC-B-100
- **spec_ref**: SPEC-B §B-BDD-1
- **depends_on**: [SPEC-A-100]
- **priority**: P0
- **estimated_complexity**: M

## Scope
为 claim_verification 任务建立带指数退避与死信队列的异步 worker,并扩展高优先级 `challenge_claim` 队列,补齐 4 个 Dashboard 指标和阈值告警,确保事实核查链路具备可观测性与故障兜底能力。

## Allowed Files
- `src/backend/workers/claim_verification_worker.py`
- `src/backend/workers/claim_verification_priority_worker.py`
- `config/celery_config.py`
- `config/alerts/claim_verification.yaml`
- `scripts/dashboard_metrics.py`
- `tests/integration/test_claim_verification_worker.py`

## Acceptance Criteria
- [ ] AC-1: 指数退避 30s → 2m → 10m;3 次失败入死信队列
- [ ] AC-2: Dashboard 输出 4 个指标:pending_count / verifying_latency_p95 / failed_rate / hard_blocking_count
- [ ] AC-3: 告警触发条件:pending > 100 或死信 > 5
- [ ] AC-4: 高优先级队列 `challenge_claim` 的延迟 p95 < 30s

## Verification Commands
```bash
pytest tests/unit/infra/test_spec_b_100.py -v
```

## Completion Definition
claim_verification worker 与高优队列均按规范实现指数退避、死信、Dashboard 指标与告警,所有集成测试通过。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/infra/test_spec_b_100.py | test_exponential_backoff_and_dead_letter |
| AC-2 | tests/unit/infra/test_spec_b_100.py | test_dashboard_emits_four_metrics |
| AC-3 | tests/unit/infra/test_spec_b_100.py | test_alert_triggers_on_pending_and_dead_letter_thresholds |
| AC-4 | tests/unit/infra/test_spec_b_100.py | test_challenge_claim_priority_queue_latency_under_30s |
