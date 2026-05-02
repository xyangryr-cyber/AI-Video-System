# [SPEC-D-013] Financial Data Service (SPEC-17)

## Metadata
- **task_id**: SPEC-D-013
- **spec_ref**: SPEC-17.1, SPEC-17.2, SPEC-17.3
- **depends_on**: [SPEC-D-003, SPEC-A-001]
- **priority**: P1
- **estimated_complexity**: M

## Scope
Implement the FinancialDataService with 3-tier fallback architecture (yfinance -> Alpha Vantage -> akshare), local cache with 30-day TTL, and Research Agent data collection enhancement. The service converts natural language queries to structured DataServiceCalls, fetches financial data with automatic source fallback, caches results in `financial_data_cache` table, and returns data as key_data_points with trust_level=source_verified. Integrates with FactChecker (SPEC-9.2.2) for data verification.

## Allowed Files
- `src/backend/services/financial_data_service.py`
- `src/backend/services/financial_data_cache.py`
- `src/backend/services/financial_providers/yfinance_provider.py`
- `src/backend/services/financial_providers/alpha_vantage_provider.py`
- `src/backend/services/financial_providers/akshare_provider.py`
- `src/backend/services/financial_providers/base_provider.py`
- `tests/unit/services/test_financial_data_service.py`
- `tests/unit/services/test_financial_data_cache.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**`
- `src/shared/schemas/**`

## Acceptance Criteria
- [ ] AC-1: 3-tier fallback: yfinance failure triggers Alpha Vantage within 10s; Alpha Vantage failure triggers akshare; all three fail -> frontend manual input form with trust_level=user_verified
- [ ] AC-2: Local cache table `financial_data_cache` with (symbol, granularity, date_range_start, date_range_end) composite unique key; TTL = 30 days (expires_at = fetched_at + 30d)
- [ ] AC-3: Cache hit -> no external HTTP request; cache expired (31+ days) -> re-fetch from external source
- [ ] AC-4: Research Agent enhancement: natural language -> structured DataServiceCall -> FinancialDataService -> key_data_point with trust_level=source_verified
- [ ] AC-5: LLM attempts to generate 6th+ data point -> rejected (enforces <= 5 llm_generated limit)
- [ ] AC-6: Returned data trust_level never equals llm_generated (always source_verified or user_verified)
- [ ] AC-7: Pre-flight check includes financial_data_service connectivity test

## Verification Commands
```bash
pytest tests/unit/pipeline/test_spec_d_013.py -v
mypy src/backend/services/financial_data_service.py --strict
```

## Completion Definition
FinancialDataService with 3-tier fallback, cache with TTL, and Research Agent integration implemented. Fallback timing verified. Cache behavior verified (hit=no HTTP, expired=re-fetch). Data point limit enforced. Pre-flight check exists. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/pipeline/test_spec_d_013.py | test_yfinance_fail_fallback_alpha_vantage |
| AC-1 | tests/unit/pipeline/test_spec_d_013.py | test_all_sources_fail_manual_input |
| AC-1 | tests/unit/pipeline/test_spec_d_013.py | test_fallback_within_10s |
| AC-2 | tests/unit/pipeline/test_spec_d_013.py | test_cache_table_composite_unique_key |
| AC-2 | tests/unit/pipeline/test_spec_d_013.py | test_cache_ttl_30_days |
| AC-3 | tests/unit/pipeline/test_spec_d_013.py | test_cache_hit_no_http |
| AC-3 | tests/unit/pipeline/test_spec_d_013.py | test_cache_expired_refetch |
| AC-4 | tests/unit/pipeline/test_spec_d_013.py | test_nl_to_data_service_call |
| AC-5 | tests/unit/pipeline/test_spec_d_013.py | test_reject_6th_llm_data_point |
| AC-6 | tests/unit/pipeline/test_spec_d_013.py | test_trust_level_never_llm_generated |
| AC-7 | tests/unit/pipeline/test_spec_d_013.py | test_preflight_check_exists |
