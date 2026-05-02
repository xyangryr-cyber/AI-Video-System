# [SPEC-B-004] async_tasks 表与任务 CRUD API

## Metadata
- **task_id**: SPEC-B-004
- **spec_ref**: SPEC-10.2, SPEC-10.6
- **depends_on**: [SPEC-A-xxx] (SPEC-1B DDL async_tasks 表, SPEC-1A API 路由), [SPEC-B-003]
- **priority**: P0
- **estimated_complexity**: M
- **bdd_tags**: [@phase4]

## Scope
实现 `async_tasks` 表的 CRUD 操作和 FIFO 调度逻辑。表包含 task_id/project_id/phase/ledger_task_id/type/params/status/progress/worker_id/attempt/max_attempts/started_at/finished_at/error 全部字段。调度按 `created_at ASC` 顺序（FIFO）。实现 `GET /api/projects/{id}/tasks` 查看队列。

## Allowed Files
- `src/backend/db/models/async_task.py`
- `src/backend/db/repositories/async_task_repo.py`
- `src/backend/api/routes/tasks.py`
- `src/backend/worker/scheduler.py`
- `tests/unit/worker/test_async_tasks.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: `async_tasks` 表存在且包含全部字段（DDL 与 SPEC-A SPEC-1B 一致）
- [ ] AC-2: `attempt` 从 1 开始，`max_attempts` 默认 3
- [ ] AC-3: 两个项目同时提交异步任务 → 按 `created_at` 顺序执行（FIFO）
- [ ] AC-4: `GET /api/projects/{id}/tasks` 返回该项目的任务列表
- [ ] AC-5: 排队中的任务 status=queued，响应包含队列位置信息（前方 N 个任务）
- [ ] AC-6: 不同项目的 async_tasks 共享同一队列

## Verification Commands
```bash
pytest tests/unit/infra/test_spec_b_004.py -v
sqlite3 data/db/app.sqlite3 ".schema async_tasks"
```

## Completion Definition
async_tasks 表 DDL 正确，FIFO 调度通过单元测试验证，任务查询 API 返回正确的队列状态。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/infra/test_spec_b_004.py | test_async_tasks_table_schema |
| AC-2 | tests/unit/infra/test_spec_b_004.py | test_attempt_starts_at_1_max_attempts_default_3 |
| AC-3 | tests/unit/infra/test_spec_b_004.py | test_fifo_scheduling_across_projects |
| AC-4 | tests/unit/infra/test_spec_b_004.py | test_get_project_tasks_api |
| AC-5 | tests/unit/infra/test_spec_b_004.py | test_queued_task_shows_position |
