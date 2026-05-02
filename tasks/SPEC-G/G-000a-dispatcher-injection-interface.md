# [SPEC-G-000a] Dispatcher 注入接口改造 — task_runner 可选参数

> **来源**: G-000-DECOMPOSITION-HANDOFF.md §2 G-000a
> **顺序**: G-000-pre → **G-000a** → G-000b

## Metadata
- **task_id**: SPEC-G-000a
- **spec_ref**: SPEC-C SPEC-3.3 (Dispatcher polling)
- **depends_on**: [SPEC-G-000-pre]
- **priority**: P0（阻塞 G-000b/c/d/e）
- **estimated_complexity**: S (~80 行)

## Scope
当前 `Dispatcher.dispatch_once()` 只把 `pending` → `queued` 状态转移（`dispatcher.py:60-74`），不调任何 worker / agent。BDD 测试需要 dispatch 后 agent 被实际执行，但生产环境又不能让 dispatcher 同步执行（违反 SPEC-B Huey 异步契约）。

本卡为 `Dispatcher.__init__` 新增可选参数 `task_runner: Callable[[str, str, dict], None] = None`，在 `dispatch_once()` 完成 `pending → queued` 状态转移后调用它。默认值由 G-000b 提供（`huey_enqueue_runner`），本卡先用一个内置 no-op runner（什么都不做，只记录调用）让 G-000a 可独立 GREEN。

**决策（禁止重新讨论）**:
- 使用 `task_runner` 注入模式，不是硬编码的 Huey 依赖
- `dispatch_once()` 在 promote 一个 task 后，**且仅当** task_runner 非 None 时，调用 `task_runner(task_id, task_type, params_dict)`

## Allowed Files
- `src/backend/engine/dispatcher.py`
- `tests/unit/backend-core/test_spec_c_003.py`（或新建 `tests/unit/backend-core/test_dispatcher_task_runner.py`）

## Forbidden Files
- `src/backend/workers/**`（留给 G-000b/c/d）
- `src/backend/engine/workflow_engine.py`
- 任何 agent 文件

## Acceptance Criteria
- [ ] AC-1: `Dispatcher.__init__` 接受 `task_runner: Optional[Callable]` 参数；未传时使用 no-op 默认值
- [ ] AC-2: `dispatch_once()` 在 promote 一个 task 后，且仅当 task_runner 非 None 时，调用 `task_runner(task_id, task_type, params_dict)`
- [ ] AC-3: 现有 single-concurrency 行为不变（`_slot_taken()` 时不调 task_runner）
- [ ] AC-4: 现有 deps 满足检查不变
- [ ] AC-5: 单测: 注入 mock task_runner，验证: 成功 promote 时被调用一次、参数正确；slot_taken 时不被调用；deps 不满足时不被调用
- [ ] AC-6: 无回归: `pytest tests/unit/backend-core/test_spec_c_003.py` 全绿
- [ ] AC-7: lint + mypy clean

## Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/backend-core/test_spec_c_003.py -v
.venv/bin/python3 -m pytest tests/unit/ -q --tb=no | tail -3
.venv/bin/ruff check src/backend/engine/dispatcher.py
.venv/bin/mypy src/backend/engine/dispatcher.py --explicit-package-bases
```

## Completion Definition
`Dispatcher` 接受可选 `task_runner` 参数。`dispatch_once()` 在 promote 后调用 `task_runner`。单并发和 deps 检查行为不变。单测覆盖 3 种调用/不调用路径。完成后追加一行 commit 记录到 `PROGRESS.md`（per HARNESS §9.2）。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1/2 | tests/unit/backend-core/test_spec_c_003.py | `test_dispatch_calls_runner_on_promote` |
| AC-3 | tests/unit/backend-core/test_spec_c_003.py | `test_dispatch_skips_runner_when_slot_taken` |
| AC-4/5 | tests/unit/backend-core/test_spec_c_003.py | `test_dispatch_skips_runner_when_deps_unmet` |

## TDD Path
1. **RED**: 加 3 个新测试到 `test_spec_c_003.py`: `test_dispatch_calls_runner_on_promote`、`test_dispatch_skips_runner_when_slot_taken`、`test_dispatch_skips_runner_when_deps_unmet`
2. Commit: `[SPEC-G-000a] RED: dispatcher task_runner injection tests`
3. **GREEN**: 在 `Dispatcher.__init__` 加参数 + `dispatch_once` 加调用
4. Commit: `[SPEC-G-000a] GREEN: dispatcher task_runner injection`
