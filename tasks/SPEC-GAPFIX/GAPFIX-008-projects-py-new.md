# [SPEC-GAPFIX-008] projects.py — 新建 CRUD router

## Metadata
- **task_id**: SPEC-GAPFIX-008
- **spec_ref**: Design Spec §3.4
- **depends_on**: [GAPFIX-005]
- **priority**: P0
- **estimated_complexity**: M

## Scope
Create `src/backend/api/routes/projects.py` with full CRUD per SPEC-1A. This is the missing router responsible for 17 of the 17 missing routes in the route diff.

## Allowed Files
- `src/backend/api/routes/projects.py`
- `tests/unit/api/test_projects_routes.py`

## Forbidden Files
- `src/backend/api/main.py` (handled by GAPFIX-011)
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `router = APIRouter(prefix="/api/projects", tags=["projects"])`
- [ ] AC-2: 实现 `GET /api/projects` (列表)
- [ ] AC-3: 实现 `POST /api/projects` (创建) — 移自 system.py
- [ ] AC-4: 实现 `GET /api/projects/{id}` (详情)
- [ ] AC-5: 实现 `GET /api/projects/{id}/state`
- [ ] AC-6: 实现 `GET /api/projects/{id}/costs`
- [ ] AC-7: 实现 `GET /api/projects/{id}/events`
- [ ] AC-8: 实现 `GET /api/projects/{id}/preferences`
- [ ] AC-9: 实现 `GET /api/projects/{id}/tasks`
- [ ] AC-10: 实现 `POST /api/projects/{id}/advance`
- [ ] AC-11: 实现 `POST /api/projects/{id}/chat`
- [ ] AC-12: 实现 `POST /api/projects/{id}/rollback`
- [ ] AC-13: 实现 `POST /api/projects/{id}/skip`
- [ ] AC-14: 实现 `DELETE /api/projects/{id}`
- [ ] AC-15: 实现 `GET /api/projects/{id}/phases/{phase_id}/artifact`
- [ ] AC-16: 实现 `POST /api/projects/{id}/preferences/confirm`
- [ ] AC-17: 实现 `POST /api/projects/{id}/tasks/{task_id}/cancel`

## Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/api/test_projects_routes.py -v
.venv/bin/python3 -m ruff check src/backend/api/routes/projects.py
.venv/bin/python3 -m mypy src/backend/api/routes/projects.py --explicit-package-bases
```

## Completion Definition
`projects.py` 存在，包含 17 个 SPEC-1A 声明的端点。所有路由测试通过。

## Implementation Notes
- 部分端点可以返回 stub 响应 (如 `{"status": "ok", "message": "not yet implemented"}`)，但路由必须注册
- `POST /api/projects` 的 `CreateProjectBody` 和 `create_project` 函数从 `system.py` 移入
- 使用 `get_db()` dependency override 模式与 system.py 一致
