# [SPEC-GAPFIX-006] observability.py — prefix 修复

## Metadata
- **task_id**: SPEC-GAPFIX-006
- **spec_ref**: Design Spec §3.2
- **depends_on**: []
- **priority**: P0
- **estimated_complexity**: M

## Scope
Fix `src/backend/api/routes/observability.py`: add `prefix="/api"` to APIRouter, change all absolute paths to relative paths.

## Allowed Files
- `src/backend/api/routes/observability.py`
- `tests/unit/api/test_observability_routes.py`

## Forbidden Files
- `src/backend/api/main.py`
- `HARNESS.md`

## Current State (from acceptance report)
```python
# router has NO prefix, decorators use absolute paths:
@router.get("/api/observability/status")
@router.get("/api/projects/{id}/events")
@router.get("/api/projects/{id}/audit")
@router.get("/api/projects/{id}/artifacts")
# main.py mounts with prefix="/api/observability" → double prefix
```

## Acceptance Criteria
- [ ] AC-1: `router = APIRouter(prefix="/api", tags=["observability"])`
- [ ] AC-2: 装饰器改为相对路径: `/observability/status`, `/projects/{project_id}/events`, `/projects/{project_id}/audit`, `/projects/{project_id}/artifacts`
- [ ] AC-3: TestClient 验证 4 个端点均返回预期响应
- [ ] AC-4: 无双层 `/api/` 前缀

## Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/api/test_observability_routes.py -v
.venv/bin/python3 -m ruff check src/backend/api/routes/observability.py
```

## Completion Definition
`observability.py` 使用 `prefix="/api"` + 相对路径装饰器，TestClient 验证 4 端点通过。

## Test Mapping
| AC | Test Function |
|----|---------------|
| AC-3 | test_observability_status_returns_200 |
| AC-3 | test_observability_events_returns_200 |
| AC-3 | test_observability_audit_returns_200 |
| AC-3 | test_observability_artifacts_returns_200 |
| AC-4 | test_observability_routes_no_double_prefix |
