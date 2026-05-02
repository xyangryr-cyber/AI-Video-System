# [SPEC-GAPFIX-012] error_handler.py — EVID_ 异常中间件

## Metadata
- **task_id**: SPEC-GAPFIX-012
- **spec_ref**: Design Spec §3.8
- **depends_on**: [GAPFIX-003]
- **priority**: P0
- **estimated_complexity**: M

## Scope
Create `src/backend/api/middleware/error_handler.py` with a unified exception handler that catches all `HTTPException` and unhandled exceptions, looks up EVID_ error codes via `lookup_evid()`, and returns structured JSON error responses.

## Allowed Files
- `src/backend/api/middleware/__init__.py` (if needed)
- `src/backend/api/middleware/error_handler.py`
- `tests/unit/api/test_error_handler.py`

## Forbidden Files
- `src/backend/api/main.py` (handled by GAPFIX-011)
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `evid_error_handler(request, exc)` 函数存在
- [ ] AC-2: HTTPException 被转换为 `{"error": {"code": "EVID_XXXX", "message": "...", "details": ...}}` 格式
- [ ] AC-3: 未处理异常返回 `EVID_1017` (Internal Server Error)
- [ ] AC-4: 响应包含正确的 HTTP status code
- [ ] AC-5: `grep -rn 'EVID_' src/backend/api/` 返回 >0 条

## Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/api/test_error_handler.py -v
.venv/bin/python3 -m ruff check src/backend/api/middleware/error_handler.py
grep -rn 'EVID_' src/backend/api/ | wc -l  # 期望 >0
```

## Completion Definition
`error_handler.py` 存在，`evid_error_handler` 函数正确转换异常为 EVID_ 格式。测试通过。`grep EVID_` 在 api/ 目录下有结果。

## Test Mapping
| AC | Test Function |
|----|---------------|
| AC-2 | test_http_exception_returns_evid_format |
| AC-3 | test_unhandled_exception_returns_evid_1017 |
| AC-4 | test_error_response_has_correct_status_code |
