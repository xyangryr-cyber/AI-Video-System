# [SPEC-GAPFIX-009] tasks.py — prefix 修复

## Metadata
- **task_id**: SPEC-GAPFIX-009
- **spec_ref**: Design Spec §3.5
- **depends_on**: []
- **priority**: P0
- **estimated_complexity**: S

## Scope
Fix `src/backend/api/routes/tasks.py`: add `prefix="/api"`, change absolute path to relative.

## Allowed Files
- `src/backend/api/routes/tasks.py`
- `tests/unit/api/test_tasks_routes.py`

## Forbidden Files
- `src/backend/api/main.py`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `router = APIRouter(prefix="/api", tags=["tasks"])`
- [ ] AC-2: 装饰器改为 `@router.get("/projects/{project_id}/tasks")`
- [ ] AC-3: TestClient 验证返回 200

## Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/api/test_tasks_routes.py -v
.venv/bin/python3 -m ruff check src/backend/api/routes/tasks.py
```

## Completion Definition
`tasks.py` 使用 `prefix="/api"` + 相对路径。测试通过。
