# [SPEC-GAPFIX-005] system.py — prefix 修复 + 移除 POST /api/projects

## Metadata
- **task_id**: SPEC-GAPFIX-005
- **spec_ref**: Design Spec §3.1
- **depends_on**: [GAPFIX-003]
- **priority**: P0
- **estimated_complexity**: M

## Scope
Fix `src/backend/api/routes/system.py`: add `prefix="/api/system"` to APIRouter, change `@router.get("/api/system/status")` to `@router.get("/status")`, remove `POST /api/projects` (will move to new `projects.py`).

## Allowed Files
- `src/backend/api/routes/system.py`
- `tests/unit/api/test_system_routes.py`

## Forbidden Files
- `src/backend/api/main.py` (handled by GAPFIX-011)
- `src/backend/api/routes/projects.py` (handled by GAPFIX-008)
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `router = APIRouter(prefix="/api/system", tags=["system"])`
- [ ] AC-2: `get_system_status` 装饰器为 `@router.get("/status")`
- [ ] AC-3: `POST /api/projects` 相关代码 (create_project, CreateProjectBody) 已移除
- [ ] AC-4: 通过 TestClient 验证 `GET /api/system/status` 返回 200
- [ ] AC-5: 通过 TestClient 验证 `POST /api/projects` 不再在 system router 上

## Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/api/test_system_routes.py -v
.venv/bin/python3 -m ruff check src/backend/api/routes/system.py
```

## Completion Definition
`system.py` 使用 `prefix="/api/system"` + 相对路径，不再包含 `POST /api/projects`。所有测试通过。

## Test Mapping
| AC | Test Function |
|----|---------------|
| AC-4 | test_get_system_status_returns_200 |
| AC-5 | test_post_projects_not_on_system_router |
