# [SPEC-GAPFIX-037] GET /api/projects 实现 (替换 501)

## Metadata
- **task_id**: SPEC-GAPFIX-037
- **spec_ref**: 第四轮扫描报告 发现 3.1; SPEC-1A
- **depends_on**: []
- **priority**: P0
- **estimated_complexity**: M

## Scope
`src/backend/api/routes/projects.py:38` 中 `list_projects()` 返回 501。前端 `useProjects.ts:12` 首屏依赖此 API 加载项目列表。

修复: 实现 `list_projects()`, 从 SQLite `projects` 表查询所有项目, 返回 `ProjectListItem[]` 格式:
```json
[{"id": "proj_xxx", "title": "...", "description": "...", "status": "...", "phase": N, "updated_at": "..."}]
```

## Allowed Files
- `src/backend/api/routes/projects.py`
- `tests/unit/backend/test_projects_list.py` (新建)

## Forbidden Files
- `src/frontend/**`
- `src/backend/db/repositories/` (本次不在 repo 层, 直接在 route 中查询 SQLite)
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `GET /api/projects` 返回 200 + JSON 数组 (非 501)
- [ ] AC-2: 返回格式包含 `id`, `title`, `description`, `phase`, `updated_at`
- [ ] AC-3: 无项目时返回空数组 `[]`
- [ ] AC-4: 使用参数化查询, 无 SQL 注入
- [ ] AC-5: `pytest tests/unit/backend/test_projects_list.py -v` 通过

## Verification Commands
```bash
# 单元测试
.venv/bin/python -m pytest tests/unit/backend/test_projects_list.py -v
# 全量回归
.venv/bin/python -m pytest tests/unit/ tests/contract/ -x --tb=short 2>&1 | tail -5
```

## Completion Definition
`GET /api/projects` 返回项目列表 JSON 数组。单元测试覆盖: 有项目/无项目/DB 错误场景。全量回归通过。

## Note
当前 `POST /projects` 在 `create_project()` 中未写 DB (只返回 mock ID)。本 card 实现 GET 时需要处理 DB 中无记录的边界情况。后续 card 应补全 POST 的 DB 写入。
