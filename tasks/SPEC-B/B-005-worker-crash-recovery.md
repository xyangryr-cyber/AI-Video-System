# [SPEC-B-005] Worker 崩溃恢复与浏览器断连容错

## Metadata
- **task_id**: SPEC-B-005
- **spec_ref**: SPEC-10.4, SPEC-10.5
- **depends_on**: [SPEC-A-xxx] (SPEC-1B DDL), [SPEC-B-003], [SPEC-B-004]
- **priority**: P0
- **estimated_complexity**: L
- **bdd_tags**: [@phase4, @performance]

## Scope
实现 Worker 崩溃恢复机制：kill -9 后 35-95s 内 retry 行出现；attempt < max_attempts 自动重试；超限置 failed。实现乐观锁 `WHERE status IN (running, queued)` 防止 cancel 竞态。确保浏览器关闭期间 Worker 不退出，重连后任务进度正确显示。

## Allowed Files
- `src/backend/worker/recovery.py`
- `src/backend/worker/tasks.py`
- `src/backend/worker/huey_config.py`
- `src/backend/db/repositories/async_task_repo.py`
- `tests/unit/worker/test_crash_recovery.py`
- `tests/integration/worker/test_browser_disconnect.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: kill -9 Worker 后 35-95s 出现 status=queued, attempt+1 的重试记录
- [ ] AC-2: Worker 重启后孤儿任务（status=running）被检测并恢复
- [ ] AC-3: attempt >= max_attempts 时任务置为 failed，不再重试
- [ ] AC-4: 乐观锁 `WHERE status IN (running, queued)` 防止 cancel 竞态
- [ ] AC-5: 浏览器关闭期间 Worker 不退出，任务继续执行
- [ ] AC-6: 浏览器重连后任务进度正确显示（从 DB 读取最新状态）

## Verification Commands
```bash
pytest tests/unit/infra/test_spec_b_005.py -v
grep -n "WHERE status IN" src/backend/db/repositories/async_task_repo.py
```

## Completion Definition
Worker 崩溃后能自动恢复任务，重试逻辑正确，竞态条件被乐观锁防护，浏览器断连不影响 Worker 运行。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/infra/test_spec_b_005.py | test_retry_appears_after_kill |
| AC-2 | tests/unit/infra/test_spec_b_005.py | test_orphan_task_recovery_on_restart |
| AC-3 | tests/unit/infra/test_spec_b_005.py | test_max_attempts_exceeded_marks_failed |
| AC-4 | tests/unit/infra/test_spec_b_005.py | test_optimistic_lock_prevents_cancel_race |
| AC-5 | tests/unit/infra/test_spec_b_005.py | test_worker_survives_browser_close |
| AC-6 | tests/unit/infra/test_spec_b_005.py | test_progress_correct_after_reconnect |
