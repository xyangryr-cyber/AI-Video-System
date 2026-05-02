# [SPEC-B-003] Huey(SqliteHuey) Worker 队列搭建

## Metadata
- **task_id**: SPEC-B-003
- **spec_ref**: SPEC-10.1, SPEC-10.3
- **depends_on**: [SPEC-A-xxx] (SPEC-1B DDL async_tasks 表), [SPEC-B-001]
- **priority**: P0
- **estimated_complexity**: M

## Scope
搭建 Huey SqliteHuey 后端，配置单 Worker 顺序执行。设置心跳参数：heartbeat=5s, scan=30s, stale_threshold=task_timeout+60s, default_max_attempts=3。配置各任务类型超时值：tts=600s, keyframe=1800s, rough=1800s, final=2400s。确保无旧版自建队列残留。

## Allowed Files
- `src/backend/worker/huey_config.py`
- `src/backend/worker/tasks.py`
- `src/backend/worker/__init__.py`
- `src/backend/core/constants.py`
- `docker-compose.yml` (worker 服务启动命令)
- `requirements.txt` / `pyproject.toml`
- `tests/unit/worker/test_huey_config.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: `data/db/` 中无旧版 `task_queue` 表
- [ ] AC-2: Worker 启动命令为 `huey_consumer` 或等效
- [ ] AC-3: heartbeat=5s, scan=30s 参数配置正确
- [ ] AC-4: stale_threshold 计算为 task_timeout + 60s
- [ ] AC-5: default_max_attempts=3
- [ ] AC-6: 超时值：tts=600s, keyframe=1800s, rough=1800s, final=2400s
- [ ] AC-7: Huey 使用 SqliteHuey 后端，DB 文件在 `data/db/` 目录

## Verification Commands
```bash
pytest tests/unit/infra/test_spec_b_003.py -v
grep -n "heartbeat\|scan\|stale_threshold\|max_attempts" src/backend/worker/huey_config.py
grep -n "task_queue" src/backend/db/ -r  # 应无结果
```

## Completion Definition
Huey SqliteHuey 配置完成，所有心跳/超时参数与规范一致，Worker 可通过 docker compose 启动。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/infra/test_spec_b_003.py | test_no_legacy_task_queue_table |
| AC-2 | tests/unit/infra/test_spec_b_003.py | test_worker_startup_command |
| AC-3 | tests/unit/infra/test_spec_b_003.py | test_heartbeat_and_scan_params |
| AC-4 | tests/unit/infra/test_spec_b_003.py | test_stale_threshold_calculation |
| AC-5 | tests/unit/infra/test_spec_b_003.py | test_default_max_attempts |
| AC-6 | tests/unit/infra/test_spec_b_003.py | test_task_timeout_values |
