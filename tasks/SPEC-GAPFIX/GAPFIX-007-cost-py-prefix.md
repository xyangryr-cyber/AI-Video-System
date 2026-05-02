# [SPEC-GAPFIX-007] cost.py — prefix 修复 + 路径改 costs

## Metadata
- **task_id**: SPEC-GAPFIX-007
- **spec_ref**: Design Spec §3.3
- **depends_on**: []
- **priority**: P0
- **estimated_complexity**: S

## Scope
Fix `src/backend/api/routes/cost.py`: add `prefix="/api"`, change path from singular `cost` to plural `costs` per SPEC-1A, fix absolute→relative path.

## Allowed Files
- `src/backend/api/routes/cost.py`
- `tests/unit/api/test_cost_routes.py`

## Forbidden Files
- `src/backend/api/main.py`
- `HARNESS.md`

## Current State (from acceptance report)
```python
# Path is "cost" (singular), SPEC requires "costs" (plural)
# Absolute path in decorator + prefix in main.py → double prefix
```

## Acceptance Criteria
- [ ] AC-1: `router = APIRouter(prefix="/api", tags=["cost"])`
- [ ] AC-2: 路径为 `/projects/{project_id}/costs` (复数)
- [ ] AC-3: TestClient 验证 `GET /api/projects/{id}/costs` 返回 200
- [ ] AC-4: 无双层前缀

## Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/api/test_cost_routes.py -v
.venv/bin/python3 -m ruff check src/backend/api/routes/cost.py
```

## Completion Definition
`cost.py` 使用 `prefix="/api"` + 相对路径 + `costs` 复数形式。测试通过。

## Test Mapping
| AC | Test Function |
|----|---------------|
| AC-3 | test_get_project_costs_returns_200 |
| AC-4 | test_cost_routes_no_double_prefix |
