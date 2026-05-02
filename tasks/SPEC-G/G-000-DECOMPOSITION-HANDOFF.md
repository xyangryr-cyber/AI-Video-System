# [SPEC-G-000] 拆解交接文档 — 给执行 AI

> **本文档身份**：交接给另一个 AI（实施 AI）的工作单。读完后，实施 AI 应当能独立完成 G-000 的全部交付。
> **创建于**：2026-04-25
> **背景作者**：上游 AI（已和许阳完成 SPEC-G 全局判断与拆解决策）
> **决策依据**：见本文末附 §A "拆解决策证据"
> **状态**：原 `tasks/SPEC-G/G-000-worker-tasks-implementation.md` **作废**（被本拆解取代），但**保留作历史参考**——不要删除原文件，在其顶端追加 `> SUPERSEDED BY G-000-DECOMPOSITION-HANDOFF.md (2026-04-25)`。

---

## 0. 实施 AI 必读：先读 / 不要做 / 必须做

### 0.1 必读（读完才能动手）
1. 本文档全文
2. `docs/specs/SPEC-G-bdd-acceptance.md`（验收上下文）
3. `docs/BDD_ANALYSIS_AND_REMEDIATION_PLAN.md`（路线图全景）
4. `HARNESS.md` §4 TDD、§9 PROGRESS、§10 CI gate
5. `src/backend/engine/dispatcher.py`（120 行，要改）
6. `src/backend/engine/workflow_engine.py`（394 行，**只读**，不改）
7. `src/backend/engine/task_types.py`（要改 enum）
8. `src/backend/workers/huey_config.py`（要扩 immediate 模式）
9. `src/backend/workers/tasks.py`（8 行，要扩为 ~300 行）
10. 6 个 phase agent 文件（**只读**接口签名）：
    - `src/backend/agents/tts_agent.py`
    - `src/backend/agents/bgm_agent.py`
    - `src/backend/agents/sfx_agent.py`
    - `src/backend/agents/keyframe_render_agent.py`
    - `src/backend/agents/rough_cut_agent.py`
    - `src/backend/agents/final_cut_agent.py`

### 0.2 不要做
- 不要直接实施原 `G-000-worker-tasks-implementation.md`——它和实际代码 6 处契约硬冲突（见 §A）
- 不要用 `huey.ImmediateHuey` 类——huey 库无此符号；要用 `huey.immediate=True` 标志
- 不要把 6 个新 task_type 直接写进 `TaskType` 枚举之外的字符串字面量——必须走 enum，否则 SPEC-3.2 校验会拒绝
- 不要在 worker 里重复 `update_task_status` 的事务逻辑——它已经处理 events 表写入
- 不要为了让测试过而绕过 `Dispatcher._slot_taken()` 单并发约束——通过 fixture 注入解决，**不动业务代码**

### 0.3 必须做
- TDD 严格执行：每个子卡 RED commit + GREEN commit（保留时序证据，per `feedback_tdd_audit_trail.md`）
- 每个子卡完成后向 `PROGRESS.md` 追加 1 行（HARNESS §9.2 格式）
- 每个子卡完成后跑该子卡 verification commands，把输出写进 commit body（HARNESS §9.3）
- 子卡之间**严格顺序执行**：pre → a → b → c → d → e

---

## 1. 拆解概览

| 子卡 ID | 标题 | 复杂度 | 依赖 | 大致行数 |
|---------|------|--------|------|---------|
| G-000-pre | TaskType 契约扩展 | S | SPEC-A/SPEC-C-002 | ~50 |
| G-000a | Dispatcher 注入接口改造 | S | G-000-pre | ~80 |
| G-000b | Huey immediate 模式 + worker 启动桥 | S | G-000a | ~60 |
| G-000c | 6 个 phase worker task 注册（NotImplementedError 占位） | M | G-000b | ~120 |
| G-000d | task → agent 真实路由（业务逻辑） | L | G-000c | ~250 |
| G-000e | agent_call_log + events 写入 + BDD conftest | M | G-000d | ~150 |
| **合计** | | | | **~710** |

**共同前置**（不属于任何子卡，但所有子卡开工前必须满足）：
- `.venv` 已重装（含 huey + numpy + jsonschema + fastapi）
- `pytest tests/unit/ -q` 至少能 collect 全部文件（17 个 collection error 必须为 0）
- 取得干净 baseline 数字写入 `docs/SPEC-D-FREEZE-2026-04-25.md`

---

## 2. 子卡详细规格

### G-000-pre：TaskType 契约扩展

#### Metadata
- **task_id**: SPEC-G-000-pre
- **spec_ref**: SPEC-A SPEC-1B (task_ledger.type DDL) + SPEC-C SPEC-3.2 (TaskType enum)
- **priority**: P0（阻塞所有 G-000 子卡）
- **complexity**: S
- **depends_on**: 无（共同前置满足后即可开工）

#### 问题陈述
`src/backend/engine/task_types.py:30` 的 `TaskType` 枚举只有 8 个标准值（`generate_artifact`/`regenerate_section`/`user_revision`/`review`/`research`/`verify`/`cross_check`/`user_annotation`）。SPEC-G2.2 要求 BDD 通过 `WorkflowEngine.create_task(task_type=...)` 调起 6 个 phase 级 task type（`generate_narration` / `preview_mix` / `plan_layout` / `render_keyframes` / `compose_rough_cut` / `export_final`）——这些 task_type **不在 enum 中**，`_validate_version_fields` 会按 "其他类型" 分支处理（无 produces/target_version 容许度），但更关键的是 SPEC-A SPEC-1B 的 task_ledger.type 列约束语义不清。

#### 决策（实施 AI 不要再讨论，直接执行）
**方案**：扩展 `TaskType` enum，新增 6 个 phase-level type 作为 `generate_artifact` 的特化变体。逻辑上它们行为等同 `generate_artifact`（允许 `produces_version`，禁止 `target_version`）。

**理由**：
- 不破坏现有 8 个 type 的语义
- BDD step 可以直接用新 type 调 `create_task`
- task_ledger.type 列原本就用 string 存，DDL 不需变（但 SPEC-A SPEC-1B 文档需要追加说明——这部分**仅文档变更**，不动 SQL）

**反方案否决理由**：
- 用 generate_artifact + params 二级路由：会让 dispatcher 判 task_type 时多绕一层，且 SPEC-G2.2 模板已写死 task_type 形态——此方案要回头修文档
- 完全在 enum 外用字符串：违反 SPEC-3.2 类型纪律

#### Allowed Files
- `src/backend/engine/task_types.py`
- `src/shared/schemas/task_ledger.json`（如存在）
- `tests/unit/backend-core/test_task_types.py`（创建/更新）

#### Forbidden Files
- 任何 `docs/specs/SPEC-*.md`（SPEC 改动留给后续 doc-only commit）
- `src/backend/engine/workflow_engine.py`
- `src/backend/api/**`
- `src/frontend/**`

#### Acceptance Criteria
- AC-1: `TaskType` 增加 6 个新枚举值：`GENERATE_NARRATION` / `PREVIEW_MIX` / `PLAN_LAYOUT` / `RENDER_KEYFRAMES` / `COMPOSE_ROUGH_CUT` / `EXPORT_FINAL`，对应字符串值见上文
- AC-2: 6 个新 type 在 `Task` Pydantic 模型的 `_validate_version_fields` 中归入 "允许 produces_version、禁止 target_version" 分支（行为等同 `generate_artifact`）
- AC-3: 单测：6 个新 type 各自能通过 Task 模型 validation；带 `target_version` 时报 `ValueError`
- AC-4: 无回归：`pytest tests/unit/backend-core/test_task_types.py` 全绿；`pytest tests/unit/ -q` 通过数 ≥ 干净 baseline

#### Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/backend-core/test_task_types.py -v
.venv/bin/python3 -m pytest tests/unit/ -q --tb=no | tail -3
.venv/bin/ruff check src/backend/engine/task_types.py
.venv/bin/mypy src/backend/engine/task_types.py
```

#### TDD 路径
1. **RED**: 在 `test_task_types.py` 加 `test_generate_narration_type_exists`、`test_preview_mix_allows_produces_version` 等 6+ 个新测试；跑应失败
2. Commit: `[SPEC-G-000-pre] RED: phase-level TaskType enum tests`
3. **GREEN**: 在 `task_types.py` 加 6 个枚举 + 在 `_validate_version_fields` 兼容分支增加新 type
4. Commit: `[SPEC-G-000-pre] GREEN: phase-level TaskType enum + Task validation`

---

### G-000a：Dispatcher 注入接口改造

#### Metadata
- **task_id**: SPEC-G-000a
- **spec_ref**: SPEC-C SPEC-3.3（Dispatcher polling）
- **priority**: P0（阻塞 G-000b/c/d/e）
- **complexity**: S
- **depends_on**: G-000-pre

#### 问题陈述
当前 `Dispatcher.dispatch_once()` 只把 `pending` → `queued` 状态转移（`dispatcher.py:60-74`），不调任何 worker / agent。BDD 测试需要 dispatch 后 agent 被实际执行，但生产环境又不能让 dispatcher 同步执行（违反 SPEC-B Huey 异步契约）。需要一个**注入式 task runner** 接口：生产注入真实 Huey enqueue，BDD 注入同步执行器。

#### 决策
- 在 `Dispatcher.__init__` 新增可选参数 `task_runner: Callable[[str, str, dict], None] = None`
- 默认值由 G-000b 提供（`huey_enqueue_runner`），G-000c 之前先用一个内置默认 runner（什么都不做，只记录调用）让 G-000a 可独立 GREEN
- `dispatch_once()` 在 `update_task_status(task_id, "queued")` 后追加：`self._task_runner(task_id, task["type"], task["params"])`

#### Allowed Files
- `src/backend/engine/dispatcher.py`
- `tests/unit/backend-core/test_spec_c_003.py`（或新建 `test_dispatcher_task_runner.py`）

#### Forbidden Files
- `src/backend/workers/**`（留给 G-000b/c/d）
- `src/backend/engine/workflow_engine.py`
- 任何 agent 文件

#### Acceptance Criteria
- AC-1: `Dispatcher(__init__)` 接受 `task_runner: Optional[Callable]` 参数；未传时使用 no-op 默认值
- AC-2: `dispatch_once()` 在 promote 一个 task 后，**且仅当** task_runner 非 None 时，调用 `task_runner(task_id, task_type, params_dict)`
- AC-3: 现有 single-concurrency 行为不变（slot_taken 时不调 task_runner）
- AC-4: 现有 deps 满足检查不变
- AC-5: 单测：注入 mock task_runner，验证：成功 promote 时被调用一次、参数正确；slot_taken 时不被调用；deps 不满足时不被调用
- AC-6: 无回归：`pytest tests/unit/backend-core/test_spec_c_003.py` 全绿
- AC-7: lint clean

#### Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/backend-core/test_spec_c_003.py -v
.venv/bin/python3 -m pytest tests/unit/ -q --tb=no | tail -3
.venv/bin/ruff check src/backend/engine/dispatcher.py
.venv/bin/mypy src/backend/engine/dispatcher.py
```

#### TDD 路径
1. **RED**: 加 3 个新测试到 `test_spec_c_003.py`：`test_dispatch_calls_runner_on_promote`、`test_dispatch_skips_runner_when_slot_taken`、`test_dispatch_skips_runner_when_deps_unmet`
2. Commit: `[SPEC-G-000a] RED: dispatcher task_runner injection tests`
3. **GREEN**: 在 `Dispatcher.__init__` 加参数 + `dispatch_once` 加调用
4. Commit: `[SPEC-G-000a] GREEN: dispatcher task_runner injection`

---

### G-000b：Huey immediate 模式 + worker 启动桥

#### Metadata
- **task_id**: SPEC-G-000b
- **spec_ref**: SPEC-B SPEC-10（worker / queue），SPEC-G2.4（BDD 同步 dispatch fixture）
- **priority**: P0
- **complexity**: S
- **depends_on**: G-000a

#### 问题陈述
- 生产 worker 用 `SqliteHuey`（`huey_config.py:48`）。BDD 在 `:memory:` 单进程中跑，不能依赖文件型 Huey。
- huey 库的同步模式开关是**实例属性** `immediate: bool`（不是单独的 `ImmediateHuey` 类，原 G-000 卡片错误）。
- 需要在 `huey_config.build_huey()` 增加 `immediate: bool = False` 参数，BDD fixture 用 `build_huey(immediate=True)`。
- 同时需要一个 `huey_enqueue_runner(huey_instance) -> Callable` 工厂，把 huey task enqueue 包装成 G-000a 期望的 `task_runner` 接口。

#### Allowed Files
- `src/backend/workers/huey_config.py`
- `src/backend/workers/run.py`（仅当需要扩展启动钩子）
- `tests/unit/infra/test_spec_b_003.py`（或新建 `test_huey_immediate_mode.py`）

#### Forbidden Files
- `src/backend/workers/tasks.py`（留给 G-000c/d）
- `src/backend/engine/**`

#### Acceptance Criteria
- AC-1: `build_huey(db_dir=None, immediate: bool = False)` 当 `immediate=True` 时返回 `SqliteHuey(..., immediate=True)`
- AC-2: 新增 `huey_enqueue_runner(huey: SqliteHuey, task_registry: dict[str, Callable]) -> Callable[[str, str, dict], None]`：根据 task_type 查 registry 拿到对应 huey task 函数，调用 `task_fn(task_id, params)`（task_fn 自身是 `@huey.task` 装饰的）
- AC-3: 单测：immediate=True 时 task 同步执行可见 side effect；immediate=False（默认）时 task 进队列不立即执行
- AC-4: lint clean

#### Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/infra/test_huey_immediate_mode.py -v
.venv/bin/ruff check src/backend/workers/huey_config.py
.venv/bin/mypy src/backend/workers/huey_config.py
```

#### TDD 路径
1. RED: 写 `test_immediate_mode_executes_synchronously` + `test_default_mode_queues_only`
2. Commit: `[SPEC-G-000b] RED: huey immediate mode + enqueue runner factory tests`
3. GREEN: 实现 `build_huey(immediate=...)` + `huey_enqueue_runner`
4. Commit: `[SPEC-G-000b] GREEN: huey immediate mode + runner factory`

---

### G-000c：6 个 phase worker task 注册（占位实现）

#### Metadata
- **task_id**: SPEC-G-000c
- **spec_ref**: SPEC-G P-1
- **priority**: P0
- **complexity**: M
- **depends_on**: G-000a + G-000b

#### 问题陈述
当前 `src/backend/workers/tasks.py` 只有 8 行 docstring。需要注册 6 个 `@huey.task` 函数，每个对应一个 phase。**本子卡先注册占位**（函数体 `raise NotImplementedError(f"phase {phase} not yet routed to agent")`），把布线、注册路径、`task_registry` 字典、TASK_TIMEOUTS 补齐这些机械性工作做完。**业务逻辑（实际调 agent）由 G-000d 完成**。

这样拆的目的：让 dispatcher → huey → task 的 wiring 链路能在 G-000c 单独 GREEN，业务路由的复杂度集中在 G-000d。

#### 关键 task_type ↔ task 函数映射
| task_type (字符串) | huey task 函数名 | TASK_TIMEOUTS key | 占位行为 |
|--------------------|-----------------|---------------------|---------|
| `generate_narration` | `run_phase4_tts` | `tts` (600s) | NotImplementedError |
| `preview_mix` | `run_phase5_bgm_preview` | **新增** `bgm` (600s 建议) | NotImplementedError |
| `plan_layout` | `run_phase6_sfx_layout` | **新增** `sfx` (600s 建议) | NotImplementedError |
| `render_keyframes` | `run_phase8_keyframe` | `keyframe` (1800s) | NotImplementedError |
| `compose_rough_cut` | `run_phase10_rough_cut` | `rough` (1800s) | NotImplementedError |
| `export_final` | `run_phase11_final_cut` | `final` (2400s) | NotImplementedError |

#### Allowed Files
- `src/backend/workers/tasks.py`
- `src/backend/workers/huey_config.py`（仅 TASK_TIMEOUTS 补齐 P5/P6）
- `tests/unit/infra/test_worker_task_registry.py`（新建）

#### Forbidden Files
- 任何 agent 文件
- `src/backend/engine/**`
- BDD 测试目录（留给 G-000e）

#### Acceptance Criteria
- AC-1: `tasks.py` 注册 6 个 `@huey.task` 函数，每个签名 `def run_phaseN_xxx(task_id: str, params: dict) -> None`，函数体仅 `raise NotImplementedError(...)`
- AC-2: `tasks.py` 暴露 `TASK_REGISTRY: dict[str, Callable]` 字典，6 个 task_type → task 函数映射
- AC-3: `TASK_TIMEOUTS` 增加 `bgm: 600` 和 `sfx: 600` key（与 SPEC-B-003 兼容）
- AC-4: 单测：每个 task_type 都能被 `TASK_REGISTRY[task_type]` 取出；调用时抛 `NotImplementedError`（这是预期）
- AC-5: 单测：`stale_threshold_for("bgm")` 和 `stale_threshold_for("sfx")` 不再 KeyError
- AC-6: lint + mypy clean
- AC-7: 无回归

#### Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/infra/test_worker_task_registry.py -v
.venv/bin/python3 -m pytest tests/unit/infra/ -q --tb=no | tail -3
.venv/bin/ruff check src/backend/workers/
.venv/bin/mypy src/backend/workers/
```

#### TDD 路径
1. RED: 写注册存在性测试 + TASK_TIMEOUTS 完整性测试
2. Commit: `[SPEC-G-000c] RED: 6 phase huey task registry tests`
3. GREEN: 实现 6 个占位 task + TASK_REGISTRY + TASK_TIMEOUTS 补齐
4. Commit: `[SPEC-G-000c] GREEN: 6 phase huey task placeholders + registry`

---

### G-000d：task → agent 真实路由（业务逻辑）

#### Metadata
- **task_id**: SPEC-G-000d
- **spec_ref**: SPEC-G P-1，SPEC-D 对应 phase
- **priority**: P0
- **complexity**: L（**子卡中最大的一张**）
- **depends_on**: G-000c
- **建议**：本卡可进一步拆为 6 张更小卡（每 phase 一张），但**不强制**——若实施 AI 评估单 context window 能完成全部 6 phase，可一次性做完。**若拆**，命名 G-000d-p4 / d-p5 / d-p6 / d-p8 / d-p10 / d-p11。

#### 问题陈述
G-000c 的 6 个 task 函数现在抛 NotImplementedError。本卡把每个 task 函数实现为：
1. 从 DB 读取 task 上下文（params + 项目状态）
2. 实例化对应 agent
3. 调用 agent 方法（按 SPEC-G2.2 表）
4. 处理返回值 / 异常
5. 通过 `WorkflowEngine.update_task_status` 写终态（succeeded / failed）
6. **不**在 worker 内手动写 events 或 agent_call_log——这些由 G-000e 处理

#### 6 个 phase 的实际 agent 调用映射

每个 task 函数实现模板：
```python
@huey.task()
def run_phase4_tts(task_id: str, params: dict) -> None:
    # 取 conn / engine（具体方式见 §3 实施 AI 注意点）
    engine = get_workflow_engine()  # singleton or context
    try:
        engine.update_task_status(task_id, "running", agent_name="TTSAgent")
        # 调 agent
        from src.backend.agents.tts_agent import TTSAgent
        agent = TTSAgent()
        result = agent.select_voice_candidates(
            polished_script=params["polished_script"],
            voice_preferences=params.get("voice_preferences"),
        )
        # （可能还要继续调 build_timeline 等，按 phase 4 的全流程）
        engine.update_task_status(task_id, "succeeded")
    except Exception as e:
        engine.update_task_status(
            task_id, "failed",
            error_code="AGENT_FAILURE",
            error_message=str(e)[:500],
        )
        raise
```

各 phase 调用细节（实施 AI 必读对应 agent 文件确认参数）：

| Phase | task 函数 | 主要 agent 方法 | params 必需字段 |
|-------|----------|---------------|----------------|
| 4 | `run_phase4_tts` | `TTSAgent().select_voice_candidates()` + `.build_timeline()` | `polished_script: dict`, `voice_preferences: dict?` |
| 5 | `run_phase5_bgm_preview` | `BGMAgent.produce_emotion_curve()` + `.select_bgm_candidates()` | `timeline: dict` |
| 6 | `run_phase6_sfx_layout` | `SFXAgent.produce_sfx()` + `.check_sparsity()` | `timeline: dict` |
| 8 | `run_phase8_keyframe` | `KeyframeRenderAgent().render_keyframes(storyboard=...)` + `.handle_failed_shot(...)` | `storyboard: list` |
| 10 | `run_phase10_rough_cut` | `RoughCutAgent.compose(...)` | （读 rough_cut_agent.compose 完整签名后填） |
| 11 | `run_phase11_final_cut` | `FinalCutAgent.adjust(rough_cut_path=..., adjustments=...)` + `.run_audit_3()` | `rough_cut_path: str`, `adjustments: dict` |

#### Allowed Files
- `src/backend/workers/tasks.py`
- `tests/unit/workers/test_phase{4,5,6,8,10,11}_tasks.py`（新建）

#### Forbidden Files
- 任何 agent 文件（**只读**，不改）
- `src/backend/engine/workflow_engine.py`（用其 API，不改）

#### Acceptance Criteria（每 phase 一组，共 6 × 3 = 18 项）
对每个 phase（4/5/6/8/10/11）：
- AC-N.1: 成功路径：mock agent 返回成功值 → task 函数执行后 `task_ledger.status = succeeded`
- AC-N.2: 失败路径：mock agent 抛异常 → `task_ledger.status = failed`，`error_code = AGENT_FAILURE`
- AC-N.3: 参数透传：params 中的字段被正确传给 agent 方法

通用：
- AC-G.1: 无回归（unit baseline 通过数不降）
- AC-G.2: lint + mypy clean

#### Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/workers/ -v
.venv/bin/python3 -m pytest tests/unit/ -q --tb=no | tail -3
.venv/bin/ruff check src/backend/workers/tasks.py
.venv/bin/mypy src/backend/workers/tasks.py
```

#### TDD 路径
建议每 phase 一个 RED-GREEN 循环（共 6 个），每个循环独立 commit：
- `[SPEC-G-000d] RED: phase4 task → TTSAgent routing tests`
- `[SPEC-G-000d] GREEN: phase4 task → TTSAgent routing`
- ...（重复 6 次）

---

### G-000e：agent_call_log + events 写入 + BDD conftest

#### Metadata
- **task_id**: SPEC-G-000e
- **spec_ref**: SPEC-G2.4，SPEC-A SPEC-1B（agent_call_log DDL）
- **priority**: P0（解锁 G-002..G-007 全部）
- **complexity**: M
- **depends_on**: G-000d

#### 问题陈述
本子卡两件事：

**Part 1（业务）**：在 worker task 函数中，agent 调用前后写入 `agent_call_log` 表（capture: agent_name, duration_ms, input_summary, output_summary, cost, tokens——见 HARNESS §8.1）。`events` 表写入由 `WorkflowEngine.update_task_status` 自动处理，无需重复。

**Part 2（BDD 基础设施）**：在 `tests/integration/bdd/conftest.py` 创建：
- `bdd_db_conn`: 跑完所有 migration 的 `:memory:` SQLite 连接（per SPEC-G1.1）
- `bdd_huey`: `build_huey(immediate=True)` 实例
- `bdd_dispatcher`: `Dispatcher(engine=engine, task_runner=huey_enqueue_runner(bdd_huey, TASK_REGISTRY))`
- `bdd_workflow_engine`: 注入 `bdd_db_conn` 的 `WorkflowEngine`

#### Allowed Files
- `src/backend/workers/tasks.py`（写 agent_call_log）
- `src/backend/services/agent_call_logger.py`（如已存在，复用；否则新建）
- `tests/integration/bdd/conftest.py`
- `tests/unit/services/test_agent_call_logger.py`（如新建 logger）

#### Forbidden Files
- BDD step 文件（**留给 G-002..G-007**）
- `src/backend/engine/**`

#### Acceptance Criteria
- AC-1: 每次 worker task 执行（成功或失败）都在 `agent_call_log` 表新增 1 行，含 8.1 节字段
- AC-2: `bdd_db_conn` fixture 跑完 5 个 migration 文件后，10 个 SPEC-G1.1 列表中的表全部存在
- AC-3: `bdd_workflow_engine` fixture 调 `create_task(task_type="generate_narration", ...)` 后，对应 agent 在同步路径下被实际调用（验证方式：mock agent + 验证调用过 1 次）
- AC-4: 至少 1 个 BDD scenario（建议 phase4 的 "TTS 应以异步长任务方式执行"）从 FAIL → PASS（这是 GREEN 终极证据）
- AC-5: 无 unit test 回归
- AC-6: lint + mypy clean
- AC-7: `verify_no_skip_stubs.py` exit 0

#### Verification Commands
```bash
.venv/bin/python3 -m pytest tests/unit/services/test_agent_call_logger.py -v
.venv/bin/python3 -m pytest tests/integration/bdd/test_phase4_bdd.py -v
.venv/bin/python3 -m pytest tests/unit/ -q --tb=no | tail -3
.venv/bin/ruff check src/backend/workers/tasks.py tests/integration/bdd/conftest.py
.venv/bin/python3 scripts/contracts/verify_no_skip_stubs.py
```

#### TDD 路径
1. RED: 写 agent_call_logger 单测 + 写 BDD conftest fixture 单测
2. Commit: `[SPEC-G-000e] RED: agent call logger + BDD conftest fixtures`
3. GREEN: 实现 logger + conftest
4. Commit: `[SPEC-G-000e] GREEN: agent call logger + BDD conftest fixtures`
5. **额外验证**：跑 phase4 BDD scenario，预期至少 1 个 PASS
6. Commit: `[SPEC-G-000e] VERIFY: phase4 BDD scenario PASS evidence`

---

## 3. 实施 AI 注意点（横切关注点）

### 3.1 WorkflowEngine 在 worker 中如何获取
worker 进程跨调用之间无共享状态。两种方案：
- **A（推荐）**: 每次 task 执行时打开新 sqlite 连接，传给 `WorkflowEngine(conn=...)`。简单、无状态。
- **B**: 用 contextvars / 线程局部变量缓存。BDD immediate 模式下要小心污染。

实施 AI 选 A，除非测试强迫用 B。选择必须在 commit body 写明理由。

### 3.2 huey 库 immediate 模式 API 校验
**实施 AI 第一步**：跑一遍以下命令确认 API：
```bash
.venv/bin/python3 -c "from huey import SqliteHuey; h = SqliteHuey('test', filename='/tmp/test_h.db', immediate=True); print('immediate=', h.immediate)"
```
若版本 < 2.5 或 immediate 参数不可用，**停下来**，向许阳报告 huey 版本问题，不要继续。

### 3.3 agent_call_log DDL 是否已存在
实施 AI **必须先检查** `src/backend/db/migrations/001_initial.sql` 是否已包含 agent_call_log 表。若包含，复用；若不包含，G-000e Part 1 还要补一个 migration（V006）。

### 3.4 单并发 (`_slot_taken`) 与 BDD 测试
BDD 测试可能同一 scenario 内创建多个 task。`_slot_taken` 检查 queued/running 状态，BDD 同步路径下 task 一旦 dispatch 立即变 succeeded，slot 释放——理论上无冲突。**但**如果出现死锁/挂起，**不要**把 `_slot_taken` 改为可绕过——通过 fixture 在每次 dispatch 前主动 reset task_ledger 来解决。

### 3.5 lint 与 mypy
HARNESS §10 要求每次 commit 前过 lint + mypy。子卡的 verification commands 已包含。**实施 AI 不能跳过任何一步**，跑红了立即修，不允许 `--no-verify`。

### 3.6 PROGRESS.md 更新
每个子卡完成后追加 1 行（HARNESS §9.2）：
```
| <sha> | SPEC-G-000-X | <imperative title> | 2026-04-XX |
```

### 3.7 Git Worktree
G-000 全部子卡在 worktree `.worktrees/spec-g-000`（分支 `feat/spec-g-000/worker-tasks`）内执行。**不要**直接在 main 上做。

---

## 4. 完成判据（整张拆解的）

- [ ] G-000-pre / a / b / c / d / e 各自的所有 AC 都过
- [ ] 至少 12 个 commit（每个子卡 ≥ 2 个：RED + GREEN；G-000d 拆 phase 时会更多）
- [ ] PROGRESS.md 追加 ≥ 6 行
- [ ] 至少 1 个 BDD scenario 从 FAIL 转 PASS（phase4 推荐）
- [ ] `pytest tests/unit/ -q` 通过数 ≥ 干净 baseline（不可降）
- [ ] `pytest tests/integration/bdd/ -q` 通过数 ≥ 8（baseline 7 + 至少 1 个新 PASS）
- [ ] 原 `G-000-worker-tasks-implementation.md` 顶部追加 SUPERSEDED 标记
- [ ] 实施 AI 在 worktree 完成所有工作后，运行 `superpowers:finishing-a-development-branch`，按四选一推进（默认建议 PR 到 main）

---

## 5. 失败 / 异常处理路径

| 情况 | 实施 AI 应做 |
|------|------------|
| huey 版本不兼容（§3.2 校验失败） | 停止，向许阳报告，不要硬改 |
| agent_call_log 表不存在且新写 migration | 在 G-000e 单独 commit 该 migration（独立 SHA） |
| 某个子卡的 unit test 跑出现回归 | **不要绕过**——退回到 RED 阶段，重新检查实现，不允许跳过失败 |
| BDD scenario 仍 FAIL 但 conftest 已绿 | 这可能意味着 SPEC-G2.2 的 step 文件需要进一步调整——**这属于 G-002..G-007 的工作**，不要在 G-000e 强行修 step 文件 |
| 实施 AI 中途发现本拆解还不够细 | 停止，把不足之处写成 markdown 反馈给许阳，等待新版拆解，**不要自行二次拆解** |

---

## §A. 拆解决策证据（背景作者留给实施 AI 的审计材料）

原 G-000 task card 与代码事实的 6 处冲突（验证日期 2026-04-25）：

| # | 原卡说法 | 代码事实（文件:行） | 严重度 |
|---|---------|-------------------|--------|
| 1 | `Dispatcher(conn=..., huey=...)` | `dispatcher.py:47` 实际签名 `(engine: WorkflowEngine, polling_interval: float)` | 致命 |
| 2 | `from huey import ImmediateHuey` | huey 库无此符号；immediate 是 `SqliteHuey(..., immediate=True)` 实例标志 | 致命 |
| 3 | 6 个新 task_type | `task_types.py:30` `TaskType` enum 只有 8 个标准值，6 个新 type 全不存在 | 致命 |
| 4 | "timeout 由 SPEC-B-003 处理" | `huey_config.py:23` `TASK_TIMEOUTS` 只有 4 个 key（tts/keyframe/rough/final），P5/P6 未配置 | 高 |
| 5 | "三表写入" | events 由 WorkflowEngine 写，agent_call_log 写入器不存在/未明 | 中 |
| 6 | "BDD `:memory:` 同步执行" | 与 `_slot_taken` 单并发约束的兼容性未表态 | 中 |

原卡缺失的设计决策：见正文 §1 引言"任务卡缺失的设计决策（≥7 项）"。

环境前置缺口（独立于本拆解，但是开工先决条件）：
- `.venv` 缺 `huey` / `numpy` / `fastapi` / `jsonschema`
- requirements.txt 缺 `huey` / `numpy`
- baseline `pytest tests/unit/ -q` 17 个 collection error，1463 passed / 23 failed（部分版本）
- 23 个历史失败列表：见 `tasks/HISTORICAL-FAILURES-PRE-G-FIX-HANDOFF.md`

---

*文档版本：v1.0*
*创建：2026-04-25*
*作废原文件指向：`tasks/SPEC-G/G-000-worker-tasks-implementation.md`（不删除，只标 SUPERSEDED）*
