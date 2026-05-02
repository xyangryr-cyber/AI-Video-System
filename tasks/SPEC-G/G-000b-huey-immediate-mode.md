# [SPEC-G-000b] Huey Immediate 模式 + Worker 启动桥

> **来源**: G-000-DECOMPOSITION-HANDOFF.md §2 G-000b
> **顺序**: G-000a → **G-000b** → G-000c

## Metadata
- **task_id**: SPEC-G-000b
- **spec_ref**: SPEC-B SPEC-10 (worker / queue) + SPEC-G2.4 (BDD 同步 dispatch fixture)
- **depends_on**: [SPEC-G-000a]
- **priority**: P0
- **estimated_complexity**: S (~60 行)

## Scope
生产 worker 用 `SqliteHuey`（`huey_config.py:48`）。BDD 在 `:memory:` 单进程中跑，不能依赖文件型 Huey。huey 库的同步模式开关是实例属性 `immediate: bool`（不是单独的 `ImmediateHuey` 类——原 G-000 卡片此点错误）。

本卡两件事:
1. `build_huey()` 增加 `immediate: bool = False` 参数，BDD fixture 用 `build_huey(immediate=True)`
2. 新增 `huey_enqueue_runner(huey, task_registry) -> Callable` 工厂，把 huey task enqueue 包装成 G-000a 期望的 `task_runner` 接口

**实施 AI 第一步**（HARD GATE — 不过就停）:
```bash
.venv/bin/python3 -c "from huey import SqliteHuey; h = SqliteHuey('test', filename='/tmp/test_h.db', immediate=True); print('immediate=', h.immediate)"
```
若 version < 2.5 或 immediate 参数不可用，停止并向许阳报告。

## Allowed Files
- `src/backend/workers/huey_config.py`
- `tests/unit/infra/test_huey_immediate_mode.py`（新建）

## Forbidden Files
- `src/backend/workers/tasks.py`（留给 G-000c/d）
- `src/backend/engine/**`

## Acceptance Criteria
- [ ] AC-1: `build_huey(db_dir=None, immediate: bool = False)` 当 `immediate=True` 时返回 `SqliteHuey(..., immediate=True)`
- [ ] AC-2: 新增 `huey_enqueue_runner(huey: SqliteHuey, task_registry: dict[str, Callable]) -> Callable[[str, str, dict], None]`: 根据 task_type 查 registry 拿到对应 huey task 函数，调用 `task_fn(task_id, params)`
- [ ] AC-3: 单测: `immediate=True` 时 task 同步执行可见 side effect；`immediate=False`（默认）时 task 进队列不立即执行
- [ ] AC-4: lint clean

## Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/infra/test_huey_immediate_mode.py -v
.venv/bin/ruff check src/backend/workers/huey_config.py
.venv/bin/mypy src/backend/workers/huey_config.py
```

## Completion Definition
`build_huey(immediate=True)` 可用。`huey_enqueue_runner` 工厂函数返回 G-000a 兼容的 `task_runner` callable。单测验证 immediate 和 default 两种模式的行为差异。完成后追加一行 commit 记录到 `PROGRESS.md`（per HARNESS §9.2）。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/infra/test_huey_immediate_mode.py | `test_build_huey_immediate_mode` |
| AC-2 | tests/unit/infra/test_huey_immediate_mode.py | `test_huey_enqueue_runner_dispatches` |
| AC-3 | tests/unit/infra/test_huey_immediate_mode.py | `test_immediate_mode_executes_synchronously` |
| AC-3 | tests/unit/infra/test_huey_immediate_mode.py | `test_default_mode_queues_only` |

## TDD Path
1. **RED**: 写 `test_immediate_mode_executes_synchronously` + `test_default_mode_queues_only` + `test_huey_enqueue_runner_dispatches`
2. Commit: `[SPEC-G-000b] RED: huey immediate mode + enqueue runner factory tests`
3. **GREEN**: 实现 `build_huey(immediate=...)` + `huey_enqueue_runner`
4. Commit: `[SPEC-G-000b] GREEN: huey immediate mode + runner factory`
