# [SPEC-GAPFIX-038] GET /api/projects/{id}/state 实现 (替换 501)

## Metadata
- **task_id**: SPEC-GAPFIX-038
- **spec_ref**: 第四轮扫描报告 发现 3.2; SPEC-1A
- **depends_on**: []
- **priority**: P0
- **estimated_complexity**: M

## Scope
`src/backend/api/routes/projects.py:74` 中 `get_project_state()` 返回 501。前端 `useProjectState.ts:8` 首屏依赖此 API 加载项目状态。

修复: 实现 `get_project_state()`, 从 SQLite 查询项目及其关联的 phases、tasks 数据, 组装 `ProjectState` 对象返回。

## Allowed Files
- `src/backend/api/routes/projects.py`
- `tests/unit/backend/test_project_state.py` (新建)

## Forbidden Files
- `src/frontend/**`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `GET /api/projects/{id}/state` 返回 200 + ProjectState JSON (非 501)
- [ ] AC-2: 返回格式符合 `src/shared/types/project_state.py` (如有) 或 SPEC-1A 定义
- [ ] AC-3: 不存在的 project_id 返回 404
- [ ] AC-4: 使用参数化查询
- [ ] AC-5: `pytest tests/unit/backend/test_project_state.py -v` 通过

## Verification Commands
```bash
# 单元测试
.venv/bin/python -m pytest tests/unit/backend/test_project_state.py -v
# 全量回归
.venv/bin/python -m pytest tests/unit/ tests/contract/ -x --tb=short 2>&1 | tail -5
```

## Completion Definition
`GET /api/projects/{id}/state` 返回项目状态对象。单元测试覆盖: 存在/不存在/多 phase 场景。全量回归通过。

## Note
如果 DB 中尚无 `projects` 表或 `phases`/`tasks` 表, 需先检查现有 migration 状态。如果表不存在, 本 card 先返回基于 fixtures 的 mock 数据 (比 501 好), 后续 card 补全 DB schema。
