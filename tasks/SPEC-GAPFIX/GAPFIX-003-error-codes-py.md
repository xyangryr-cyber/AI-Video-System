# [SPEC-GAPFIX-003] error_codes.py — 17 个 EVID_ 错误码映射

## Metadata
- **task_id**: SPEC-GAPFIX-003
- **spec_ref**: Design Spec §2.3
- **depends_on**: []
- **priority**: P0
- **estimated_complexity**: S

## Scope
Define 17 EVID_ error codes → HTTP status code → user message mapping table in `src/shared/contracts/error_codes.py`, per SPEC-13A.

## Allowed Files
- `src/shared/contracts/error_codes.py`
- `tests/unit/contracts/test_error_codes.py`

## Forbidden Files
- `src/backend/api/**`
- `src/frontend/**`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: 定义恰好 17 个 EVID_ 错误码 (EVID_1001..EVID_1017)
- [ ] AC-2: 每个错误码映射到正确的 HTTP status code (400/404/409/422/500/503)
- [ ] AC-3: `lookup_evid(evid_code: str) -> dict` 函数返回 `{"code", "status", "message"}` dict
- [ ] AC-4: 不存在的 EVID_ code 返回 500 fallback

## Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/contracts/test_error_codes.py -v
.venv/bin/python3 -c "from src.shared.contracts.error_codes import lookup_evid; print(lookup_evid('EVID_1001'))"
```

## Completion Definition
`error_codes.py` 包含 17 个 EVID_ 错误码映射表 + `lookup_evid()` 函数。所有测试通过。

## Test Mapping
| AC | Test Function |
|----|---------------|
| AC-1 | test_exactly_17_error_codes |
| AC-2 | test_error_code_http_status_mapping |
| AC-3 | test_lookup_evid_returns_dict |
| AC-4 | test_lookup_evid_unknown_returns_500 |
