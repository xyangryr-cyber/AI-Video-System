# [SPEC-B-007] agent_call_log 表与成本聚合

## Metadata
- **task_id**: SPEC-B-007
- **spec_ref**: SPEC-13.1, SPEC-13.2
- **depends_on**: [SPEC-A-xxx] (SPEC-1B DDL agent_call_log 表, SPEC-1A cost API), [SPEC-B-001]
- **priority**: P1
- **estimated_complexity**: M

## Scope
实现 `agent_call_log` 表（agent_name/tokens/duration_ms/phase/project_id/model/prompt(脱敏)/response(脱敏)/created_at）。每次 LLM 调用后自动写入。实现按 project_id 和 phase 的成本聚合查询。超 $15 WARN 日志但不熔断（V1）。

## Allowed Files
- `src/backend/db/models/agent_call_log.py`
- `src/backend/db/repositories/agent_call_log_repo.py`
- `src/backend/core/llm_client.py` (装饰器/中间件写入日志)
- `src/backend/api/routes/cost.py`
- `src/backend/core/cost_aggregator.py`
- `tests/unit/infra/test_agent_call_log.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: 每次 LLM 调用后 `agent_call_log` 自动写入一行
- [ ] AC-2: `tokens` 为正整数，`duration_ms` 为实际测量值（非硬编码）
- [ ] AC-3: 按 phase 的成本之和等于 `total_cost_usd`（`by_phase` 聚合一致性）
- [ ] AC-4: 单项目 LLM 成本超 $15 时输出 WARN 日志
- [ ] AC-5: V1 无熔断逻辑（超 $15 不中断任务）

## Verification Commands
```bash
pytest tests/unit/infra/test_spec_b_007.py -v
sqlite3 data/db/app.sqlite3 ".schema agent_call_log"
grep -n "circuit_break\|fuse\|熔断" src/backend/ -r  # 应无结果
```

## Completion Definition
agent_call_log 表自动记录每次 LLM 调用，成本聚合查询正确，$15 告警不熔断。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/infra/test_spec_b_007.py | test_auto_log_on_llm_call |
| AC-2 | tests/unit/infra/test_spec_b_007.py | test_tokens_positive_duration_measured |
| AC-3 | tests/unit/infra/test_spec_b_007.py | test_by_phase_sum_equals_total |
| AC-4 | tests/unit/infra/test_spec_b_007.py | test_cost_warn_at_15_dollars |
| AC-5 | tests/unit/infra/test_spec_b_007.py | test_no_circuit_breaker_v1 |
