# [SPEC-G-000c] 6 个 Phase Worker Task 注册（占位实现）

> **来源**: G-000-DECOMPOSITION-HANDOFF.md §2 G-000c
> **顺序**: G-000b → **G-000c** → G-000d

## Metadata
- **task_id**: SPEC-G-000c
- **spec_ref**: SPEC-G P-1
- **depends_on**: [SPEC-G-000a, SPEC-G-000b]
- **priority**: P0
- **estimated_complexity**: M (~120 行)

## Scope
当前 `src/backend/workers/tasks.py` 只有 8 行 docstring。本卡注册 6 个 `@huey.task` 函数，每个对应一个 phase，**函数体为占位**（`raise NotImplementedError(...)`），把布线、注册路径、`TASK_REGISTRY` 字典、`TASK_TIMEOUTS` 补齐这些机械性工作做完。

**业务逻辑（实际调 agent）由 G-000d 完成**。这样拆的目的: 让 dispatcher → huey → task 的 wiring 链路能在 G-000c 单独 GREEN，业务路由的复杂度集中在 G-000d。

### task_type ↔ task 函数映射

| task_type (字符串) | huey task 函数名 | TASK_TIMEOUTS key | 占位行为 |
|--------------------|-----------------|---------------------|---------|
| `generate_narration` | `run_phase4_tts` | `tts` (600s, 已存在) | `NotImplementedError` |
| `preview_mix` | `run_phase5_bgm_preview` | `bgm` (600s, **新增**) | `NotImplementedError` |
| `plan_layout` | `run_phase6_sfx_layout` | `sfx` (600s, **新增**) | `NotImplementedError` |
| `render_keyframes` | `run_phase8_keyframe` | `keyframe` (1800s, 已存在) | `NotImplementedError` |
| `compose_rough_cut` | `run_phase10_rough_cut` | `rough` (1800s, 已存在) | `NotImplementedError` |
| `export_final` | `run_phase11_final_cut` | `final` (2400s, 已存在) | `NotImplementedError` |

## Allowed Files
- `src/backend/workers/tasks.py`
- `src/backend/workers/huey_config.py`（仅 TASK_TIMEOUTS 补齐 P5/P6）
- `tests/unit/infra/test_worker_task_registry.py`（新建）

## Forbidden Files
- 任何 agent 文件
- `src/backend/engine/**`
- BDD 测试目录（留给 G-000e）

## Acceptance Criteria
- [ ] AC-1: `tasks.py` 注册 6 个 `@huey.task` 函数，每个签名 `def run_phaseN_xxx(task_id: str, params: dict) -> None`，函数体仅 `raise NotImplementedError(...)`
- [ ] AC-2: `tasks.py` 暴露 `TASK_REGISTRY: dict[str, Callable]` 字典，6 个 task_type → task 函数映射
- [ ] AC-3: `TASK_TIMEOUTS` 增加 `bgm: 600` 和 `sfx: 600` key（与 SPEC-B-003 兼容）
- [ ] AC-4: 单测: 每个 task_type 都能被 `TASK_REGISTRY[task_type]` 取出；调用时抛 `NotImplementedError`（这是预期行为）
- [ ] AC-5: 单测: `stale_threshold_for("bgm")` 和 `stale_threshold_for("sfx")` 不再 KeyError
- [ ] AC-6: lint + mypy clean
- [ ] AC-7: 无回归

## Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/infra/test_worker_task_registry.py -v
.venv/bin/python3 -m pytest tests/unit/infra/ -q --tb=no | tail -3
.venv/bin/ruff check src/backend/workers/
.venv/bin/mypy src/backend/workers/
```

## Completion Definition
`tasks.py` 包含 6 个 `@huey.task` 占位函数 + `TASK_REGISTRY` 字典。`TASK_TIMEOUTS` 补齐 `bgm`/`sfx`。wiring 链路 dispatcher → huey → task registry 可被单测验证。完成后追加一行 commit 记录到 `PROGRESS.md`（per HARNESS §9.2）。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/infra/test_worker_task_registry.py | `test_all_6_tasks_registered` |
| AC-2 | tests/unit/infra/test_worker_task_registry.py | `test_registry_maps_each_task_type` |
| AC-2 | tests/unit/infra/test_worker_task_registry.py | `test_registry_callable_raises_not_implemented` |
| AC-3 | tests/unit/infra/test_worker_task_registry.py | `test_task_timeouts_has_bgm_and_sfx` |
| AC-5 | tests/unit/infra/test_worker_task_registry.py | `test_stale_threshold_for_bgm_no_keyerror` |
| AC-5 | tests/unit/infra/test_worker_task_registry.py | `test_stale_threshold_for_sfx_no_keyerror` |

## TDD Path
1. **RED**: 写注册存在性测试 + TASK_TIMEOUTS 完整性测试
2. Commit: `[SPEC-G-000c] RED: 6 phase huey task registry tests`
3. **GREEN**: 实现 6 个占位 task + TASK_REGISTRY + TASK_TIMEOUTS 补齐
4. Commit: `[SPEC-G-000c] GREEN: 6 phase huey task placeholders + registry`
