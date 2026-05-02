# [SPEC-GAPFIX-010] preferences.py — prefix 修复

## Metadata
- **task_id**: SPEC-GAPFIX-010
- **spec_ref**: Design Spec §3.6
- **depends_on**: []
- **priority**: P0
- **estimated_complexity**: S

## Scope
Fix `src/backend/api/routes/preferences.py`: add `prefix="/api"`, change absolute path to relative.

## Allowed Files
- `src/backend/api/routes/preferences.py`
- `tests/unit/api/test_preferences_routes.py`

## Forbidden Files
- `src/backend/api/main.py`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `router = APIRouter(prefix="/api", tags=["preferences"])`
- [ ] AC-2: 装饰器改为 `@router.get("/projects/{project_id}/preferences")`
- [ ] AC-3: TestClient 验证返回 200

## Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/api/test_preferences_routes.py -v
.venv/bin/python3 -m ruff check src/backend/api/routes/preferences.py
```

## Completion Definition
`preferences.py` 使用 `prefix="/api"` + 相对路径。测试通过。
