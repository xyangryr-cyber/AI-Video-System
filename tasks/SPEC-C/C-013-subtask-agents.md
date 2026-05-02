# [SPEC-C-013] Generic SubTask Agents (Research, Verify, CrossCheck) & FinancialData

## Metadata
- **task_id**: SPEC-C-013
- **spec_ref**: SPEC-6.1, SPEC-6.2, SPEC-6.3, SPEC-6.4, SPEC-6.5
- **depends_on**: [SPEC-A-001, SPEC-C-001, SPEC-C-011]
- **priority**: P1
- **estimated_complexity**: L

## Scope
Implement three SubTask agents (ResearchAgent, DataVerifyAgent, CrossCheckAgent) callable via `inject_subtask` from any phase. Enforce constraints: 180s timeout, Research 3-5 sources, CrossCheck max 20 diffs (truncate+mark), DataVerify confidence 2 decimal places. Results injected into next Router prompt as <=800 token supplementary_context. SubTask failures do NOT block GateKeeper. Also integrate FinancialDataService with 3-tier fallback (yfinance -> Alpha Vantage -> akshare), 30-day SQLite cache, and max 5 LLM data points.

## Allowed Files
- `src/backend/agents/subtask_agents.py`
- `src/backend/agents/research_agent.py`
- `src/backend/agents/data_verify_agent.py`
- `src/backend/agents/cross_check_agent.py`
- `src/backend/services/financial_data_service.py`
- `tests/unit/backend-core/test_subtask_agents.py`
- `tests/unit/backend-core/test_financial_data.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: All 3 agents callable via `inject_subtask` from any phase
- [ ] AC-2: Results written to `task_ledger.result_ref`
- [ ] AC-3: Exceeding 180s forces task status to `timeout`
- [ ] AC-4: Research produces 3-5 sources
- [ ] AC-5: CrossCheck diffs capped at 20, excess truncated with `truncated` flag
- [ ] AC-6: DataVerify confidence has exactly 2 decimal places
- [ ] AC-7: SubTask result injected into Router prompt as <=800 tokens (auto-truncated)
- [ ] AC-8: SubTask failure does NOT cause GateKeeper to fail (other conditions met)
- [ ] AC-9: FinancialDataService falls back yfinance -> Alpha Vantage -> akshare
- [ ] AC-10: Financial data cached in SQLite with 30-day TTL
- [ ] AC-11: LLM output with >5 data points is rejected (not written)

## Verification Commands
```bash
pytest tests/unit/backend-core/test_spec_c_013.py -v
ruff check src/backend/agents/subtask_agents.py src/backend/services/financial_data_service.py
mypy src/backend/agents/subtask_agents.py src/backend/services/financial_data_service.py --strict
```

## Completion Definition
Three SubTask agents work from any phase with all constraints enforced. Results inject into Router context. Failures don't block gates. FinancialDataService has 3-tier fallback and caching. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/backend-core/test_spec_c_013.py | test_inject_subtask_any_phase |
| AC-2 | tests/unit/backend-core/test_spec_c_013.py | test_result_written_to_result_ref |
| AC-3 | tests/unit/backend-core/test_spec_c_013.py | test_timeout_180s |
| AC-4 | tests/unit/backend-core/test_spec_c_013.py | test_research_3_to_5_sources |
| AC-5 | tests/unit/backend-core/test_spec_c_013.py | test_crosscheck_max_20_diffs |
| AC-6 | tests/unit/backend-core/test_spec_c_013.py | test_verify_confidence_2_decimals |
| AC-7 | tests/unit/backend-core/test_spec_c_013.py | test_router_injection_max_800_tokens |
| AC-8 | tests/unit/backend-core/test_spec_c_013.py | test_subtask_fail_gate_still_passes |
| AC-9 | tests/unit/backend-core/test_spec_c_013.py | test_fallback_chain |
| AC-10 | tests/unit/backend-core/test_spec_c_013.py | test_cache_30_day_ttl |
| AC-11 | tests/unit/backend-core/test_spec_c_013.py | test_reject_over_5_data_points |
