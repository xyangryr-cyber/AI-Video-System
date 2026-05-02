# [SPEC-G-000e] Agent Call Log 写入 + BDD Conftest Fixture

> **来源**: G-000-DECOMPOSITION-HANDOFF.md §2 G-000e
> **顺序**: G-000d → **G-000e**（G-000 拆解最后一张子卡，完成后解锁 G-002..G-007）

## Metadata
- **task_id**: SPEC-G-000e
- **spec_ref**: SPEC-G2.4 (BDD Sync Dispatch Fixture) + SPEC-A SPEC-1B (agent_call_log DDL)
- **depends_on**: [SPEC-G-000d]
- **priority**: P0（解锁 G-002..G-007 全部）
- **estimated_complexity**: M (~150 行)

## Scope
本卡两件事:

### Part 1 — agent_call_log 写入（业务）
在 worker task 函数中，agent 调用前后写入 `agent_call_log` 表。字段（per HARNESS §8.1）: `agent_name`, `duration_ms`, `input_summary`, `output_summary`, `cost`, `tokens`。

**注意**: `events` 表写入由 `WorkflowEngine.update_task_status` 自动处理，**不要在 worker 内重复实现**。

### Part 2 — BDD 基础设施
在 `tests/integration/bdd/conftest.py` 创建:
- `bdd_db_conn`: 跑完所有 migration 的 `:memory:` SQLite 连接（per SPEC-G1.1）
- `bdd_huey`: `build_huey(immediate=True)` 实例
- `bdd_dispatcher`: `Dispatcher(engine=engine, task_runner=huey_enqueue_runner(bdd_huey, TASK_REGISTRY))`
- `bdd_workflow_engine`: 注入 `bdd_db_conn` 的 `WorkflowEngine`

## Allowed Files
- `src/backend/workers/tasks.py`（写 agent_call_log）
- `src/backend/services/agent_call_logger.py`（如已存在，复用；否则新建）
- `tests/integration/bdd/conftest.py`
- `tests/unit/services/test_agent_call_logger.py`（如新建 logger）

## Forbidden Files
- BDD step 文件（**留给 G-002..G-007**）
- `src/backend/engine/**`

## Acceptance Criteria
- [ ] AC-1: 每次 worker task 执行（成功或失败）都在 `agent_call_log` 表新增 1 行，含 HARNESS §8.1 字段
- [ ] AC-2: `bdd_db_conn` fixture 跑完 5 个 migration 文件后，10 个 SPEC-G1.1 列表中的表全部存在
- [ ] AC-3: `bdd_workflow_engine` fixture 调 `create_task(task_type="generate_narration", ...)` 后，对应 agent 在同步路径下被实际调用（验证方式: mock agent + 验证调用过 1 次）
- [ ] AC-4: 至少 1 个 BDD scenario（建议 phase4 的 "TTS 应以异步长任务方式执行"）从 FAIL → PASS（这是 GREEN 终极证据）
- [ ] AC-5: 无 unit test 回归
- [ ] AC-6: lint + mypy clean
- [ ] AC-7: `verify_no_skip_stubs.py` exit 0

## Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/services/test_agent_call_logger.py -v
.venv/bin/python3 -m pytest tests/integration/bdd/test_phase4_bdd.py -v
.venv/bin/python3 -m pytest tests/unit/ -q --tb=no | tail -3
.venv/bin/ruff check src/backend/workers/tasks.py tests/integration/bdd/conftest.py
.venv/bin/python3 scripts/contracts/verify_no_skip_stubs.py
```

## Completion Definition
`agent_call_log` 表在每次 worker task 执行时被写入。BDD conftest 提供 4 个 fixture（`bdd_db_conn`, `bdd_huey`, `bdd_dispatcher`, `bdd_workflow_engine`）。至少 1 个 BDD scenario 从 FAIL 转 PASS。完成后追加一行 commit 记录到 `PROGRESS.md`（per HARNESS §9.2）。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/services/test_agent_call_logger.py | `test_log_written_on_success` |
| AC-1 | tests/unit/services/test_agent_call_logger.py | `test_log_written_on_failure` |
| AC-2 | tests/integration/bdd/conftest.py | `bdd_db_conn` fixture (10 tables exist) |
| AC-3 | tests/integration/bdd/conftest.py | `bdd_workflow_engine` fixture (agent called synchronously) |
| AC-4 | tests/integration/bdd/test_phase4_bdd.py | phase4 BDD scenario PASS |

## TDD Path
1. **RED**: 写 agent_call_logger 单测 + 写 BDD conftest fixture 单测
2. Commit: `[SPEC-G-000e] RED: agent call logger + BDD conftest fixtures`
3. **GREEN**: 实现 logger + conftest
4. Commit: `[SPEC-G-000e] GREEN: agent call logger + BDD conftest fixtures`
5. **额外验证**: 跑 phase4 BDD scenario，预期至少 1 个 PASS
6. Commit: `[SPEC-G-000e] VERIFY: phase4 BDD scenario PASS evidence`

## 实施 AI 前置检查

1. **agent_call_log DDL 是否存在**: 必须先检查 `src/backend/db/migrations/001_initial.sql` 是否已包含 `agent_call_log` 表。若包含，复用；若不包含，本卡 Part 1 还要补一个 migration（V006），**单独 commit 该 migration**（独立 SHA）。
2. **单并发与 BDD**: BDD 同步路径下 task 一旦 dispatch 立即变 succeeded，slot 释放——理论上无冲突。但如果出现死锁/挂起，**不要**把 `_slot_taken` 改为可绕过——通过 fixture 在每次 dispatch 前主动 reset task_ledger 来解决。
