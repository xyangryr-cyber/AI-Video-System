# SPEC-A API 路由对齐与前端集成 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 OpenAPI 已实现的端点与 SPEC-1A 路由总表完全对齐，新增 4 个 ProjectList/ProjectDetail 页面所需的端点（GET /api/projects、GET /api/projects/{id}、GET /api/projects/{id}/state、WS /ws/{project_id} accept 层），前端清掉错误的 `/api/v1/` 前缀并通过 vite proxy 联通，浏览器打开 `localhost:3000` 不再"加载失败"。

**Architecture:**
- 后端：将 `routes/*.py` 装饰器统一改为相对路径（settings_bridge 风格），main.py include 时只带模块前缀；新增 `routes/projects.py`、`routes/websocket.py`；注册被遗漏的 `api/preferences.py`。
- 前端：`vite.config.ts` 加 `server.proxy` 把 `/api` 和 `/ws` 转发到 backend；移除所有 hooks/components/types/mocks 中的 `/v1/` 字面量；WebSocket 路径相对化，去掉 hardcode `localhost:8000`。
- WS 桥接：本 plan 仅实现 WS endpoint 的连接层（accept、保持、心跳）；EventBus → WS 的事件广播桥接 deferred 到后续 Plan B。

**Tech Stack:** FastAPI (backend) / Pydantic / sqlite3 / pytest+httpx / Vite 6 / React 18 / @tanstack/react-query / MSW (mocks) / TypeScript / vitest

---

## Authority & Compliance

- **Ground truth**：`docs/specs/SPEC-A-contracts.md` SPEC-1A 路由总表（25 endpoints）+ SPEC-0A.3 ProjectState schema + SPEC-11A WS envelope（仅 envelope 形态，事件广播 deferred）。
- **HARNESS 合规**：
  - §4 TDD：T4-T7（新端点）走 RED→GREEN→REFACTOR→COMMIT；T1-T3、T8-T10（路径/配置）走 §4.3 TDD 例外（配置类）但仍需 verification。
  - §1.1 目录授权：本 plan 改动的所有路径都在 allowed 范围内（`src/backend/**`、`src/frontend/**`、`tests/**`、`PROGRESS.md`）；不触碰 forbidden（`HARNESS.md` / `CLAUDE.md` / `docs/specs/**`）。
  - §2 依赖方向：所有改动遵守 Layer 0→7 单向依赖；前后端通过 `src/shared/` + REST/WS 通信，无跨层 import。
  - §3.2 commit prefix：本 plan 跨 SPEC-A（契约对齐）、SPEC-C（API 实现）、SPEC-E（前端集成）。task 编号采用 `SPEC-INTEG-001..SPEC-INTEG-010`（集成修复专用，不占用 tasks/SPEC-X/ 卡片号）。**首次执行前需 user 确认此编号约定**，或改用最贴近 SPEC 的现有未占用号（如 `[SPEC-C-100..]` / `[SPEC-E-100..]`）。
  - §6 文件大小：所有新建文件 < 300 行（前端）/ 400 行（后端）。
  - §9 PROGRESS.md：每个 task commit 后追加一行 `| <sha> | SPEC-INTEG-NNN | <title> | YYYY-MM-DD |`。
  - §10 CI：每个 task 跑 `pytest tests/unit/backend/api/` + `pnpm --filter frontend test`；最终 task 跑 madge 循环依赖检查。

---

## Out of Scope (Deferred to Follow-up Plans)

明确**不做**的事项，避免 scope creep：

| 项目 | 原因 | Follow-up Plan |
|---|---|---|
| FSM 操作端点（advance / skip / rollback / chat） | 涉及 SPEC-D pipeline 状态机，需独立深度对齐 | **Plan D** |
| `DELETE /api/projects/{id}` | 软删除规则要确认 SPEC-C 中 archived/deleted 状态机 | Plan D |
| `POST /api/projects/{id}/tasks/{task_id}/cancel` | 任务账本副作用，需对齐 SPEC-C 任务调度 | Plan D |
| `POST /api/projects/{id}/preferences/confirm` | 涉及 PreferenceService 决策写入路径 | Plan D |
| `GET /api/projects/{id}/phases/{phase}/artifact` | 静态文件服务+签名 URL，归 SPEC-B-NNN | Plan D 或 SPEC-B 后续卡 |
| EventBus → WS 事件广播桥接 | 需要 in-process pubsub registry + WorkflowEngine sink hook，独立做更稳 | **Plan B** (SPEC-11A 完整对齐) |
| HTTP 错误码体系（17 codes） | 横切，本 plan 只用 FastAPI 默认 4xx/5xx | **Plan C** (SPEC-13A) |
| 统一 JSON 日志格式 | 横切，本 plan 不强制 | Plan C (SPEC-13B) |

**本 plan 完成后预期状态**：
- ✅ 浏览器打开 `localhost:3000` 显示 ProjectList 页（含 0 个或多个项目卡片，不再"加载失败"）
- ✅ 创建项目能成功（POST 路径已存在，本 plan 修对前缀后即可用）
- ✅ 点击项目卡片进入 PhaseDetail 页（GET state 返回完整 ProjectState）
- ✅ WS 连接建立成功（前端 useProjects 不报 connection error）
- ⚠️  WS 不会推送实际事件（Plan B 范畴，本 plan 接受这个边界）
- ⚠️  推进/跳过/回退/聊天按钮点击会 404（Plan D 范畴）

---

## File Structure Map

### Backend

| 文件 | 操作 | 责任 |
|---|---|---|
| `src/backend/api/main.py` | Modify | router include prefix 重整；注册 `api/preferences.py`、`routes/projects.py`、`routes/websocket.py` |
| `src/backend/api/routes/system.py` | Modify | 装饰器路径相对化（`/api/system/status` → `/status`，`/api/projects` → 移到 projects.py） |
| `src/backend/api/routes/tasks.py` | Modify | 装饰器路径相对化（`/api/projects/{id}/tasks` → `/{project_id}/tasks`） |
| `src/backend/api/routes/preferences.py` | Modify | 装饰器路径相对化 |
| `src/backend/api/routes/observability.py` | Modify | 装饰器路径相对化（events/audit/artifacts 三处） |
| `src/backend/api/routes/cost.py` | Modify | 装饰器路径相对化 + `cost`→`costs` |
| `src/backend/api/preferences.py` | Modify | 装饰器路径相对化（writeback-suggestions） |
| `src/backend/api/routes/projects.py` | **Create** | `GET /api/projects` 列表 + `GET /api/projects/{id}` 详情 + `GET /api/projects/{id}/state` 完整状态 |
| `src/backend/api/routes/websocket.py` | **Create** | `WS /ws/{project_id}`：accept、心跳、连接保持（事件广播 deferred） |

### Frontend

| 文件 | 操作 | 责任 |
|---|---|---|
| `src/frontend/vite.config.ts` | Modify | 加 `server.proxy` 把 `/api` 和 `/ws` 转发到 backend |
| `src/frontend/hooks/useProjects.ts` | Modify | URL 去掉 `/v1` |
| `src/frontend/hooks/useCreateProject.ts` | Modify | URL 去掉 `/v1` |
| `src/frontend/hooks/useProjectState.ts` | Modify | URL 去掉 `/v1` |
| `src/frontend/hooks/useEventStream.ts` | Modify | URL 去掉 `/v1` |
| `src/frontend/hooks/usePreferenceWriteback.ts` | Modify | URL 去掉 `/v1`（2 处） |
| `src/frontend/hooks/useMasterAudioSubscription.ts` | Modify | WS 路径 `/ws/projects/{id}` → `/ws/{id}` |
| `src/frontend/components/CandidateSelector.tsx` | Modify | URL 去掉 `/v1` |
| `src/frontend/types/project.ts` | Modify | 注释更新（去 `/v1`） |
| `src/frontend/mocks/handlers.ts` | Modify | URL 去掉 `/v1`（5 处） |
| `src/frontend/pages/ProjectList.tsx` | Modify | WS URL 相对化（去 `localhost:8000`、去 `/projects`） |

### Tests

| 文件 | 操作 | 责任 |
|---|---|---|
| `tests/unit/backend/api/test_routes_path_alignment.py` | **Create** | 快照测试：OpenAPI paths 与 SPEC-1A 已实现端点列表完全相符 |
| `tests/unit/backend/api/test_projects_route.py` | **Create** | GET /api/projects + GET /api/projects/{id} + GET /api/projects/{id}/state 三端点单测 |
| `tests/unit/backend/api/test_websocket_route.py` | **Create** | WS /ws/{project_id} accept + 心跳测试 |
| `tests/unit/backend/api/test_system_route.py` | Modify | 路径从 `/api/system/api/system/status` 更新为 `/api/system/status` |
| `tests/unit/backend/api/test_tasks_route.py` | Modify | 同上路径更新 |
| `tests/unit/backend/api/test_preferences_route.py` | Modify | 同上路径更新 |
| `tests/unit/backend/api/test_observability_route.py` | Modify | 同上路径更新 |
| `tests/unit/backend/api/test_cost_route.py` | Modify | 同上路径更新 + cost→costs |
| `tests/unit/frontend/**` | Modify | mocks/hooks 路径更新（依赖 MSW handlers） |

> **注意**：现有 backend api 测试文件名实际可能与上表略有出入。Task 1 的 Step 1 会先 `ls tests/unit/backend/api/` 列出真实文件，再针对真实文件名进行更新。

---

## Tasks

### Task 1: OpenAPI 路径对齐契约测试（RED 基线）

**Why first**：这是**契约门控**——本 plan 所有后端路径变更都要让此测试由 RED 走到 GREEN，不能跳过。

**Files:**
- Create: `tests/unit/backend/api/test_routes_path_alignment.py`

- [ ] **Step 1: 列出现有 backend api 测试文件清单**

Run: `ls tests/unit/backend/api/ 2>/dev/null`
Expected: 看到现有 test_*.py 文件清单（用于后续 task 修改路径时锁定文件名）。记录到 plan 执行笔记。

- [ ] **Step 2: 创建路径对齐契约测试**

```python
# tests/unit/backend/api/test_routes_path_alignment.py
"""[SPEC-INTEG-001] OpenAPI 路径与 SPEC-1A 路由总表的对齐快照测试。

仅断言"已实现端点"与 SPEC-1A 中对应行的路径字面量一致。
缺失端点（advance/skip/rollback/chat 等）属于 Plan D 范畴，
不在本测试覆盖之内。
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from src.backend.api.main import app


# SPEC-A SPEC-1A 路由总表中"本 plan 应该让 OpenAPI 暴露"的端点集合。
EXPECTED_PATHS_AFTER_PLAN_A = {
    # System / Health
    ("GET", "/health"),
    ("GET", "/api/system/status"),
    # Projects (本 plan 新增)
    ("GET", "/api/projects"),
    ("POST", "/api/projects"),
    ("GET", "/api/projects/{project_id}"),
    ("GET", "/api/projects/{project_id}/state"),
    # Tasks (现有，修对前缀后)
    ("GET", "/api/projects/{project_id}/tasks"),
    # Preferences (现有，修对前缀后)
    ("GET", "/api/projects/{project_id}/preferences"),
    ("POST", "/api/projects/{project_id}/preferences/writeback-suggestions"),
    # Observability (现有，修对前缀后)
    ("GET", "/api/observability/status"),
    ("GET", "/api/projects/{project_id}/events"),
    ("GET", "/api/projects/{project_id}/audit"),
    ("GET", "/api/projects/{project_id}/artifacts"),
    # Cost (现有，修对前缀+复数化)
    ("GET", "/api/projects/{project_id}/costs"),
    # Settings (已对齐，纳入快照)
    ("GET", "/api/settings"),
    ("PUT", "/api/settings/model-config"),
    ("PUT", "/api/settings/brand-kit"),
    ("GET", "/api/settings/preferences"),
    ("PUT", "/api/settings/preferences"),
    ("GET", "/api/settings/preferences/snapshots"),
    ("POST", "/api/settings/preferences/snapshots/{snapshot_id}/rollback"),
}


def test_openapi_paths_match_spec_1a_for_implemented_endpoints() -> None:
    client = TestClient(app)
    spec = client.get("/openapi.json").json()
    actual: set[tuple[str, str]] = set()
    for path, ops in spec.get("paths", {}).items():
        for method in ops:
            actual.add((method.upper(), path))

    missing = EXPECTED_PATHS_AFTER_PLAN_A - actual
    superfluous_double_prefix = {
        (m, p) for (m, p) in actual
        if "/api/system/api/" in p or "/api/tasks/api/" in p
        or "/api/observability/api/" in p or "/api/cost/api/" in p
        or "/api/projects/api/" in p
    }

    assert not missing, f"缺失端点: {sorted(missing)}"
    assert not superfluous_double_prefix, (
        f"双前缀路径仍存在: {sorted(superfluous_double_prefix)}"
    )
```

- [ ] **Step 3: 运行测试验证它失败（RED）**

Run: `cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && pytest tests/unit/backend/api/test_routes_path_alignment.py -v`
Expected: FAIL，输出形如 `缺失端点: [('GET', '/api/projects'), ('GET', '/api/projects/{project_id}'), ...]` + `双前缀路径仍存在: [...]`。这正是本 plan 要消除的状态。

- [ ] **Step 4: 不实现，先 commit RED 测试作为基线**

```bash
git add tests/unit/backend/api/test_routes_path_alignment.py
git commit -m "[SPEC-INTEG-001] add OpenAPI path alignment contract test (RED baseline)

Files Changed:
- tests/unit/backend/api/test_routes_path_alignment.py

Verification:
- pytest tests/unit/backend/api/test_routes_path_alignment.py -v -> FAIL (expected, RED baseline)

Decisions:
- 用快照式 tuple set 而非逐个端点用例，便于后续 task 增删端点时一处更新。
- 双前缀检测用启发式匹配 (/api/X/api/) 覆盖所有当前已知错误模式。

Artifacts:
- 契约测试 EXPECTED_PATHS_AFTER_PLAN_A: 21 条端点"
```

- [ ] **Step 5: 追加 PROGRESS.md 一行**

Append to `PROGRESS.md` 的 Recent commits 表：
```
| <short-sha> | SPEC-INTEG-001 | add OpenAPI path alignment contract test | 2026-04-26 |
```
Run: `git add PROGRESS.md && git commit --amend --no-edit`（合入上一个 commit）。

---

### Task 2: 后端路由装饰器统一相对路径（消除双前缀）

**Files:**
- Modify: `src/backend/api/main.py:33-40`
- Modify: `src/backend/api/routes/system.py:39,61`
- Modify: `src/backend/api/routes/tasks.py:56`
- Modify: `src/backend/api/routes/preferences.py:46`
- Modify: `src/backend/api/routes/observability.py:25,32,52,67`
- Modify: `src/backend/api/routes/cost.py:22`
- Modify: 现有受影响测试（路径从双前缀更新到单前缀）

- [ ] **Step 1: 修改 main.py 的 include_router 为带 module-prefix 风格**

```python
# src/backend/api/main.py 第 33-40 行替换为：
app.include_router(system.router, prefix="/api/system", tags=["system"])
app.include_router(tasks.router, prefix="/api/projects", tags=["tasks"])
app.include_router(preferences.router, prefix="/api/projects", tags=["preferences"])
app.include_router(observability.router, tags=["observability"])
app.include_router(cost.router, prefix="/api/projects", tags=["cost"])
app.include_router(settings_bridge.router)
```

注意 observability 不带 prefix 因为它要同时暴露 `/api/observability/status` 和 `/api/projects/{id}/...`，统一在装饰器上写完整路径（observability 是唯一例外，因路由跨命名空间）。

> **system.py 即将拆分**：`POST /api/projects` 在当前 system.py 第 61 行，将由 Task 4 移到新的 `routes/projects.py`；本 task 暂保留在 system.py 但路径改为 `/projects`（被 main.py prefix `/api/system` 加成 `/api/system/projects`）——这是临时态，Task 4 会移除。**为保证 Task 2 commit 后 OpenAPI 不会同时丢失 POST /api/projects**，本 task 只移装饰器路径，不动函数；Task 4 把整段函数移走，并在 system.py 删除 import 残留。

- [ ] **Step 2: 修改 routes/system.py 装饰器**

```python
# src/backend/api/routes/system.py 第 39 行替换：
@router.get("/status")
def get_system_status(...

# 第 61 行替换（临时态，Task 4 移除）：
@router.post("/projects", status_code=201)  # 注意：会被 /api/system 前缀加成 /api/system/projects
def create_project(...
```

> 临时态期间 OpenAPI 会同时出现 `POST /api/system/projects` 和（Task 4 后的）`POST /api/projects`。Task 4 的 commit 必须在 Task 2 后立即执行，避免长时间双暴露。

- [ ] **Step 3: 修改 routes/tasks.py 装饰器**

```python
# src/backend/api/routes/tasks.py 第 56 行替换：
@router.get("/{project_id}/tasks")
def list_project_tasks(...
```

- [ ] **Step 4: 修改 routes/preferences.py 装饰器**

```python
# src/backend/api/routes/preferences.py 第 46 行替换：
@router.get("/{project_id}/preferences")
def get_project_preferences(...
```

- [ ] **Step 5: 修改 routes/observability.py 装饰器（4 处）**

```python
# src/backend/api/routes/observability.py
# 第 25 行：保留绝对路径，因 main.py 此 router 不带 prefix
@router.get("/api/observability/status")

# 第 32 行：
@router.get("/api/projects/{project_id}/events")

# 第 52 行：
@router.get("/api/projects/{project_id}/audit")

# 第 67 行：
@router.get("/api/projects/{project_id}/artifacts")
```

- [ ] **Step 6: 修改 routes/cost.py 装饰器（含路径修正 cost→costs）**

```python
# src/backend/api/routes/cost.py 第 22 行替换：
@router.get("/{project_id}/costs")
def get_project_cost(...
```

- [ ] **Step 7: 跑 OpenAPI 路径对齐测试 + 现有受影响测试**

Run: `pytest tests/unit/backend/api/ -v`
Expected: 部分用例可能挂（路径硬编码在测试里），记录失败列表。`test_routes_path_alignment.py` 的 `双前缀` 断言应通过，但 `缺失端点` 仍 FAIL（projects 系列还没实现）。

- [ ] **Step 8: 修复现有测试的硬编码路径**

对每个失败测试文件（Step 1 列出过的清单），把测试请求中的双前缀路径改为单前缀：
- `/api/system/api/system/status` → `/api/system/status`
- `/api/system/api/projects` → `/api/system/projects`（临时态，Task 4 后再调到 `/api/projects`）
- `/api/tasks/api/projects/{id}/tasks` → `/api/projects/{id}/tasks`
- `/api/projects/api/projects/{id}/preferences` → `/api/projects/{id}/preferences`
- `/api/observability/api/...` → `/api/observability/status` 或 `/api/projects/{id}/events|audit|artifacts`
- `/api/cost/api/projects/{id}/cost` → `/api/projects/{id}/costs`

- [ ] **Step 9: 跑全量 backend 单测**

Run: `pytest tests/unit/backend/ -x -q`
Expected: PASS（除了 `test_routes_path_alignment.py` 中"缺失端点"断言仍 FAIL，这是预期的——Task 4-6 才实现）。

- [ ] **Step 10: Commit**

```bash
git add src/backend/api/ tests/unit/backend/api/
git commit -m "[SPEC-INTEG-002] align route decorators to relative-path style; eliminate double prefix

Files Changed:
- src/backend/api/main.py
- src/backend/api/routes/system.py
- src/backend/api/routes/tasks.py
- src/backend/api/routes/preferences.py
- src/backend/api/routes/observability.py
- src/backend/api/routes/cost.py
- tests/unit/backend/api/test_*.py (路径硬编码更新)

Verification:
- pytest tests/unit/backend/ -x -q -> PASS（路径对齐测试中缺失端点断言仍 FAIL，预期，Task 4-6 实现）
- curl http://localhost:8000/openapi.json | jq '.paths | keys' -> 不再含 /api/system/api/、/api/tasks/api/、/api/cost/api/ 等双前缀

Decisions:
- observability router 不在 main.py 加 prefix，因其同时暴露 /api/observability/* 和 /api/projects/{id}/* 跨命名空间端点。
- POST /api/projects 临时停留在 system.py（路径 /api/system/projects），Task 4 移除。
- cost 路径单数 cost 改为复数 costs 与 SPEC-1A 一致。

Artifacts:
- 6 个 routes 文件 + main.py 路径前缀语义清晰化
- OpenAPI 双前缀消除（验证：grep '/api/X/api/' 无结果）"
```

PROGRESS.md 追加一行，amend 进 commit。

---

### Task 3: 注册被遗漏的 preferences writeback-suggestions 模块

**Files:**
- Modify: `src/backend/api/main.py:15`（import） + main.py include_router
- Modify: `src/backend/api/preferences.py:52` （装饰器路径相对化）

- [ ] **Step 1: 修改 src/backend/api/preferences.py 装饰器**

读 `src/backend/api/preferences.py:52` 实际装饰器 path，改为相对路径：
```python
# src/backend/api/preferences.py 第 52 行附近
@router.post(
    "/{project_id}/preferences/writeback-suggestions",
    response_model=WritebackSuggestionsResponse,
)
def post_writeback_suggestions(...
```

- [ ] **Step 2: 在 main.py 注册该 router**

```python
# src/backend/api/main.py 第 15 行 import 列表加：
from src.backend.api.routes import cost, observability, preferences, settings_bridge, system, tasks
from src.backend.api import preferences as preferences_writeback  # 新增

# 第 36 行附近（observability 后）追加：
app.include_router(
    preferences_writeback.router, prefix="/api/projects", tags=["preferences-writeback"]
)
```

- [ ] **Step 3: 跑 OpenAPI 路径对齐测试**

Run: `pytest tests/unit/backend/api/test_routes_path_alignment.py -v`
Expected: `缺失端点` 断言中 `('POST', '/api/projects/{project_id}/preferences/writeback-suggestions')` 不再出现（仍有 projects 系列缺失，预期）。

- [ ] **Step 4: 跑该端点已有测试（如果有）**

Run: `pytest tests/unit/backend/ -k "writeback" -v`
Expected: 已有测试 PASS（如果之前测试用占位 client 跑过它就要更新路径；如果之前测试根本调不通它，本次会暴露并需修）。

- [ ] **Step 5: Commit**

```bash
git add src/backend/api/main.py src/backend/api/preferences.py tests/
git commit -m "[SPEC-INTEG-003] register preferences writeback-suggestions router

Files Changed:
- src/backend/api/main.py
- src/backend/api/preferences.py

Verification:
- pytest tests/unit/backend/api/test_routes_path_alignment.py -v -> writeback endpoint 进入 OpenAPI

Decisions:
- import alias 'preferences_writeback' 避免与 routes/preferences.py 同名冲突。
- prefix='/api/projects' 与 routes/preferences.py 共享，因路径都是 /api/projects/{id}/preferences/...

Artifacts:
- POST /api/projects/{project_id}/preferences/writeback-suggestions 暴露在 OpenAPI"
```

PROGRESS.md 追加一行，amend。

---

### Task 4: 新建 routes/projects.py 并实现 GET /api/projects（列表）

**Why TDD**：新增端点，HARNESS §4.1 强制 RED→GREEN→REFACTOR→COMMIT。

**Files:**
- Create: `src/backend/api/routes/projects.py`
- Create: `tests/unit/backend/api/test_projects_route.py`
- Modify: `src/backend/api/main.py`（注册新 router；从 system.py 删除 POST /projects 相关代码）
- Modify: `src/backend/api/routes/system.py`（删除 CreateProjectBody + create_project 函数）

- [ ] **Step 1: 写 RED 测试 — GET /api/projects**

```python
# tests/unit/backend/api/test_projects_route.py
"""[SPEC-INTEG-004] GET /api/projects 列表端点单测。

SPEC 引用: SPEC-A SPEC-1A 第 380 行 `GET /api/projects -> {projects: Project[]}`
"""
from __future__ import annotations

import sqlite3
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.backend.api.main import app


@pytest.fixture
def client_with_seeded_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    """Create a temp sqlite, run schema.sql, seed 2 projects, override get_db()."""
    db_path = tmp_path / "test.sqlite3"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    schema_sql = Path("src/backend/db/schema.sql").read_text()
    conn.executescript(schema_sql)
    conn.execute(
        "INSERT INTO projects (project_id, title, description, current_phase, status) "
        "VALUES (?, ?, ?, ?, ?)",
        ("proj_001", "Demo A", "desc-A-aaaaaaaaaa", 0, "active"),
    )
    conn.execute(
        "INSERT INTO projects (project_id, title, description, current_phase, status) "
        "VALUES (?, ?, ?, ?, ?)",
        ("proj_002", "Demo B", "desc-B-bbbbbbbbbb", 3, "active"),
    )
    conn.commit()

    from src.backend.api.routes import projects as projects_module

    def _override_get_db() -> sqlite3.Connection:
        return conn

    monkeypatch.setattr(projects_module, "get_db", _override_get_db)
    app.dependency_overrides[projects_module.get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        conn.close()


def test_list_projects_returns_seeded_projects(client_with_seeded_db: TestClient) -> None:
    resp = client_with_seeded_db.get("/api/projects")
    assert resp.status_code == 200
    body = resp.json()
    assert "projects" in body
    ids = {p["project_id"] for p in body["projects"]}
    assert ids == {"proj_001", "proj_002"}


def test_list_projects_excludes_deleted(client_with_seeded_db: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """soft-deleted projects should not appear in list."""
    from src.backend.api.routes import projects as projects_module
    conn = projects_module.get_db()
    conn.execute("UPDATE projects SET status='deleted' WHERE project_id='proj_001'")
    conn.commit()

    resp = client_with_seeded_db.get("/api/projects")
    assert resp.status_code == 200
    ids = {p["project_id"] for p in resp.json()["projects"]}
    assert ids == {"proj_002"}, "deleted projects must not be listed"


def test_list_projects_returns_required_fields(client_with_seeded_db: TestClient) -> None:
    resp = client_with_seeded_db.get("/api/projects")
    body = resp.json()
    p = next(p for p in body["projects"] if p["project_id"] == "proj_002")
    for field in ("project_id", "title", "description", "current_phase", "status", "created_at", "updated_at"):
        assert field in p, f"projects[].{field} missing"
    assert p["current_phase"] == 3
    assert p["status"] == "active"
```

- [ ] **Step 2: 跑测试验证 RED**

Run: `pytest tests/unit/backend/api/test_projects_route.py -v`
Expected: FAIL with `ModuleNotFoundError: src.backend.api.routes.projects` 或 `404 Not Found`。

- [ ] **Step 3: 创建 routes/projects.py 实现 GET /api/projects**

```python
# src/backend/api/routes/projects.py
"""[SPEC-INTEG-004] Projects API routes.

Routes:
- GET /api/projects               list all non-deleted projects
- GET /api/projects/{project_id}  get single project (Task 5)
- GET /api/projects/{project_id}/state  full ProjectState (Task 6)

Authority: SPEC-A SPEC-1A (路由总表) + SPEC-0A.3 (ProjectState schema)
"""
from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()


def get_db() -> sqlite3.Connection:  # pragma: no cover -- app wiring
    """Wired in main.py via dependency_overrides at runtime."""
    raise RuntimeError("get_db not wired; main.py should override this dependency")


def _row_to_project_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "project_id": row["project_id"],
        "title": row["title"],
        "description": row["description"],
        "current_phase": row["current_phase"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@router.get("")
def list_projects(db: sqlite3.Connection = Depends(get_db)) -> dict[str, Any]:
    """SPEC-1A: GET /api/projects -> {projects: Project[]}."""
    db.row_factory = sqlite3.Row
    cur = db.execute(
        "SELECT project_id, title, description, current_phase, status, "
        "       created_at, updated_at "
        "FROM projects "
        "WHERE status != 'deleted' "
        "ORDER BY updated_at DESC"
    )
    rows = cur.fetchall()
    return {"projects": [_row_to_project_dict(r) for r in rows]}
```

- [ ] **Step 4: 在 main.py 注册新 router 并接 db dependency**

```python
# src/backend/api/main.py 修改：
# import 列表追加：
from src.backend.api.routes import cost, observability, preferences, projects, settings_bridge, system, tasks

# include_router 部分追加（在 system 那行后面）：
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])

# 添加全局 db dependency 桥接（在 include_router 之前）：
import sqlite3
from pathlib import Path
import os

def _get_db_connection() -> sqlite3.Connection:
    db_url = os.environ.get("DATABASE_URL", "sqlite:///./data/db/dev.sqlite3")
    db_path = db_url.replace("sqlite:///", "").replace("sqlite:////", "/")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

app.dependency_overrides[projects.get_db] = _get_db_connection
```

> **注意**：现有 system.py / tasks.py 等文件都有自己的 `get_db()` 函数（`# pragma: no cover -- app wiring`），实际生产时应该有统一的 db dependency provider。本 plan **不重构这部分**，仅按现有风格添加 projects.get_db 的 wiring。如果发现项目已有统一的 `src/backend/db/` provider，复用之。

- [ ] **Step 5: 跑测试验证 GREEN**

Run: `pytest tests/unit/backend/api/test_projects_route.py -v`
Expected: 3 个测试 PASS。

- [ ] **Step 6: 删除 system.py 中的 POST /api/projects（已被 projects.py 取代）**

```python
# src/backend/api/routes/system.py
# 删除：CreateProjectBody class 定义
# 删除：@router.post("/projects", ...) 装饰的 create_project 函数
# 保留：@router.get("/status") 装饰的 get_system_status 函数
```

- [ ] **Step 7: 在 routes/projects.py 重新实现 POST /api/projects（迁移）**

```python
# src/backend/api/routes/projects.py 末尾追加：
from pydantic import BaseModel, Field


class CreateProjectBody(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=10)


@router.post("", status_code=201)
def create_project(
    body: CreateProjectBody,
    db: sqlite3.Connection = Depends(get_db),
) -> dict[str, str]:
    """SPEC-1A: POST /api/projects -> {project_id}."""
    import uuid
    project_id = f"proj_{uuid.uuid4().hex[:8]}"
    db.execute(
        "INSERT INTO projects (project_id, title, description, current_phase, status) "
        "VALUES (?, ?, ?, 0, 'active')",
        (project_id, body.title, body.description),
    )
    db.commit()
    return {"project_id": project_id}
```

- [ ] **Step 8: 跑全 backend 单测 + 路径对齐测试**

Run: `pytest tests/unit/backend/ -x -q`
Expected: PASS。`test_routes_path_alignment.py`：`/api/projects` 出现且不缺失。

- [ ] **Step 9: Commit**

```bash
git add src/backend/api/ tests/unit/backend/api/test_projects_route.py
git commit -m "[SPEC-INTEG-004] add GET /api/projects (list) + migrate POST /api/projects to routes/projects.py

Files Changed:
- src/backend/api/routes/projects.py (new)
- src/backend/api/routes/system.py (removed CreateProjectBody/create_project)
- src/backend/api/main.py (register projects router + db wiring)
- tests/unit/backend/api/test_projects_route.py (new, 3 cases)

Verification:
- pytest tests/unit/backend/api/test_projects_route.py -v -> 3 PASS
- pytest tests/unit/backend/ -x -q -> all PASS
- curl http://localhost:8000/api/projects -> {\"projects\":[...]} (after dev server reload)

Decisions:
- POST /api/projects 从 system.py 移到 projects.py 与 GET 同模块管理，符合 SPEC-1A 命名空间。
- list_projects 默认按 updated_at DESC 排序（前端 ProjectList 期望新项目在前）。
- 软删除：WHERE status != 'deleted' 保证返回不含已删项目。

Artifacts:
- GET /api/projects (list)
- POST /api/projects (migrated from system.py)"
```

---

### Task 5: 新增 GET /api/projects/{project_id}（详情）

**Files:**
- Modify: `src/backend/api/routes/projects.py`
- Modify: `tests/unit/backend/api/test_projects_route.py`

- [ ] **Step 1: 追加 RED 测试**

```python
# tests/unit/backend/api/test_projects_route.py 末尾追加：

def test_get_project_returns_full_project(client_with_seeded_db: TestClient) -> None:
    resp = client_with_seeded_db.get("/api/projects/proj_002")
    assert resp.status_code == 200
    body = resp.json()
    assert body["project_id"] == "proj_002"
    assert body["title"] == "Demo B"
    assert body["current_phase"] == 3


def test_get_project_404_for_unknown_id(client_with_seeded_db: TestClient) -> None:
    resp = client_with_seeded_db.get("/api/projects/proj_does_not_exist")
    assert resp.status_code == 404


def test_get_project_404_for_deleted_status(client_with_seeded_db: TestClient) -> None:
    from src.backend.api.routes import projects as projects_module
    conn = projects_module.get_db()
    conn.execute("UPDATE projects SET status='deleted' WHERE project_id='proj_001'")
    conn.commit()
    resp = client_with_seeded_db.get("/api/projects/proj_001")
    assert resp.status_code == 404
```

- [ ] **Step 2: 跑 RED**

Run: `pytest tests/unit/backend/api/test_projects_route.py::test_get_project_returns_full_project -v`
Expected: FAIL with 404（路由未实现）。

- [ ] **Step 3: 实现 GET /api/projects/{project_id}**

```python
# src/backend/api/routes/projects.py 在 list_projects 后追加：

@router.get("/{project_id}")
def get_project(
    project_id: str,
    db: sqlite3.Connection = Depends(get_db),
) -> dict[str, Any]:
    """SPEC-1A: GET /api/projects/{id} -> Project."""
    db.row_factory = sqlite3.Row
    cur = db.execute(
        "SELECT project_id, title, description, current_phase, status, "
        "       created_at, updated_at "
        "FROM projects "
        "WHERE project_id = ? AND status != 'deleted'",
        (project_id,),
    )
    row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"project {project_id!r} not found")
    return _row_to_project_dict(row)
```

- [ ] **Step 4: 跑 GREEN**

Run: `pytest tests/unit/backend/api/test_projects_route.py -v`
Expected: 全部 PASS（5 个用例）。

- [ ] **Step 5: Commit**

```bash
git add src/backend/api/routes/projects.py tests/unit/backend/api/test_projects_route.py
git commit -m "[SPEC-INTEG-005] add GET /api/projects/{project_id} detail endpoint

Files Changed:
- src/backend/api/routes/projects.py (+get_project)
- tests/unit/backend/api/test_projects_route.py (+3 cases)

Verification:
- pytest tests/unit/backend/api/test_projects_route.py -v -> 5 PASS

Decisions:
- 404 用 FastAPI 默认 HTTPException；SPEC-13A 错误码体系 deferred to Plan C。
- 软删除项目视为不存在 (404)，与 list 行为一致。

Artifacts:
- GET /api/projects/{project_id}"
```

---

### Task 6: 新增 GET /api/projects/{project_id}/state（完整 ProjectState）

**Why complex**：SPEC-0A.3 要求返回完整 ProjectState（含 phases 数组、preferences、artifact_url 等）。本 task 实现**最小可工作版本**：返回 project + phases 数组。其他字段（candidates、verification_records 等）填空数组，由 Plan B/C 完整化。

**Files:**
- Modify: `src/backend/api/routes/projects.py`
- Modify: `tests/unit/backend/api/test_projects_route.py`

- [ ] **Step 1: 读 SPEC-0A.3 ProjectState schema 确认必填字段**

Run: `sed -n '121,170p' docs/specs/SPEC-A-contracts.md`
记录所需顶层字段（如 `project`、`phases`、`current_phase`、`latest_reached_phase` 等）。

- [ ] **Step 2: 追加 RED 测试**

```python
# tests/unit/backend/api/test_projects_route.py 末尾追加：

def test_get_project_state_returns_minimal_schema(
    client_with_seeded_db: TestClient,
) -> None:
    """SPEC-0A.3: ProjectState 必备顶层字段 (本 plan 实现最小可工作版本)。"""
    resp = client_with_seeded_db.get("/api/projects/proj_002/state")
    assert resp.status_code == 200
    state = resp.json()
    # 必备顶层字段（SPEC-0A.3）：
    assert "project" in state
    assert "phases" in state
    assert state["project"]["project_id"] == "proj_002"
    assert state["project"]["current_phase"] == 3
    # phases 即使为空也必须是 list（不能是 None）
    assert isinstance(state["phases"], list)


def test_get_project_state_404_for_unknown_id(client_with_seeded_db: TestClient) -> None:
    resp = client_with_seeded_db.get("/api/projects/proj_nope/state")
    assert resp.status_code == 404


def test_get_project_state_includes_seeded_phases(
    client_with_seeded_db: TestClient,
) -> None:
    """如有 phases 表 row，应出现在 state.phases。"""
    from src.backend.api.routes import projects as projects_module
    conn = projects_module.get_db()
    # 插入一行 phase 数据（schema 字段以实际为准；执行时如字段名不符需调）
    conn.execute(
        "INSERT INTO phases (project_id, phase_num, status, artifact_path) "
        "VALUES (?, ?, ?, ?)",
        ("proj_002", 0, "completed", "/tmp/p0.json"),
    )
    conn.commit()
    resp = client_with_seeded_db.get("/api/projects/proj_002/state")
    body = resp.json()
    phase_nums = [p["phase_num"] for p in body["phases"]]
    assert 0 in phase_nums
```

> **注意**：`phases` 表的实际列名以 `src/backend/db/schema.sql` 中的 `CREATE TABLE phases` 为准。Step 1 需先 `sed -n '/CREATE TABLE phases/,/^);/p' src/backend/db/schema.sql` 拿到准确列名，必要时调整 INSERT 语句和断言字段。

- [ ] **Step 3: 跑 RED**

Run: `pytest tests/unit/backend/api/test_projects_route.py -k state -v`
Expected: FAIL（404 或 AttributeError）。

- [ ] **Step 4: 实现 GET /api/projects/{project_id}/state**

```python
# src/backend/api/routes/projects.py 末尾追加：

@router.get("/{project_id}/state")
def get_project_state(
    project_id: str,
    db: sqlite3.Connection = Depends(get_db),
) -> dict[str, Any]:
    """SPEC-1A: GET /api/projects/{id}/state -> ProjectState (SPEC-0A.3).

    本 plan 实现最小可工作版本：返回 project + phases 数组。
    其他字段（candidates / verification_records / preferences 等）
    deferred to Plan B/C 与对应实现端点接通后回填。
    """
    db.row_factory = sqlite3.Row
    proj_cur = db.execute(
        "SELECT project_id, title, description, current_phase, status, "
        "       created_at, updated_at "
        "FROM projects WHERE project_id = ? AND status != 'deleted'",
        (project_id,),
    )
    proj_row = proj_cur.fetchone()
    if proj_row is None:
        raise HTTPException(status_code=404, detail=f"project {project_id!r} not found")

    phases_cur = db.execute(
        "SELECT * FROM phases WHERE project_id = ? ORDER BY phase_num ASC",
        (project_id,),
    )
    phases = [dict(r) for r in phases_cur.fetchall()]

    return {
        "project": _row_to_project_dict(proj_row),
        "phases": phases,
        # Deferred fields per SPEC-0A.3:
        # "candidates": [],  # Plan B/C
        # "verification_records": [],  # Plan B/C
        # "preferences": {},  # Plan B/C (existing /api/projects/{id}/preferences endpoint)
    }
```

- [ ] **Step 5: 跑 GREEN**

Run: `pytest tests/unit/backend/api/test_projects_route.py -v`
Expected: 全部 PASS（8 个用例）。

- [ ] **Step 6: Commit**

```bash
git add src/backend/api/routes/projects.py tests/unit/backend/api/test_projects_route.py
git commit -m "[SPEC-INTEG-006] add GET /api/projects/{project_id}/state minimal ProjectState

Files Changed:
- src/backend/api/routes/projects.py (+get_project_state)
- tests/unit/backend/api/test_projects_route.py (+3 cases)

Verification:
- pytest tests/unit/backend/api/test_projects_route.py -v -> 8 PASS
- pytest tests/unit/backend/api/test_routes_path_alignment.py -v -> PASS（projects 系列全到位）

Decisions:
- 最小可工作版本：返回 project + phases，其他 SPEC-0A.3 字段（candidates/verification_records 等）留空，
  由 Plan B/C 接入相应数据源后填充。前端 PhaseDetail 页此时能渲染 phases 导航条。
- 软删除项目视为 404，与 GET /api/projects/{id} 一致。

Artifacts:
- GET /api/projects/{project_id}/state (minimal)"
```

---

### Task 7: 新增 WS /ws/{project_id}（accept + 心跳，事件广播 deferred）

**Why deferred broadcast**：完整 EventBus → WS 桥接需要 in-process pubsub registry + WorkflowEngine sink hook，工作量超出本 plan 边界。本 task 实现 accept 层让前端连接不报错，事件广播由 Plan B 实现。

**Files:**
- Create: `src/backend/api/routes/websocket.py`
- Create: `tests/unit/backend/api/test_websocket_route.py`
- Modify: `src/backend/api/main.py`（注册 WS）

- [ ] **Step 1: 写 RED 测试**

```python
# tests/unit/backend/api/test_websocket_route.py
"""[SPEC-INTEG-007] WS /ws/{project_id} accept + heartbeat 单测。

本 plan 仅断言：
  1. WS 端点接受连接（不返回 404）
  2. 服务端发送一个 envelope-shaped greeting（用于前端判定连通性）
  3. 服务端响应客户端 ping 心跳

事件广播 (phase.advanced/status.changed 等) deferred to Plan B (SPEC-11A)。
"""
from __future__ import annotations

import json

from fastapi.testclient import TestClient

from src.backend.api.main import app


def test_ws_accepts_connection_and_sends_greeting() -> None:
    client = TestClient(app)
    with client.websocket_connect("/ws/proj_test_123") as ws:
        msg = ws.receive_text()
        envelope = json.loads(msg)
        # SPEC-11A WsEventEnvelope 形状: { type, project_id, timestamp, payload }
        assert envelope["type"] == "ws.connected"
        assert envelope["project_id"] == "proj_test_123"
        assert "timestamp" in envelope
        assert "payload" in envelope


def test_ws_responds_to_ping() -> None:
    client = TestClient(app)
    with client.websocket_connect("/ws/proj_ping") as ws:
        ws.receive_text()  # consume greeting
        ws.send_text(json.dumps({"type": "ping"}))
        msg = ws.receive_text()
        envelope = json.loads(msg)
        assert envelope["type"] == "pong"
        assert envelope["project_id"] == "proj_ping"
```

- [ ] **Step 2: 跑 RED**

Run: `pytest tests/unit/backend/api/test_websocket_route.py -v`
Expected: FAIL with 404 或 connection error。

- [ ] **Step 3: 创建 routes/websocket.py**

```python
# src/backend/api/routes/websocket.py
"""[SPEC-INTEG-007] WebSocket endpoint - accept + heartbeat layer.

本模块仅实现 SPEC-1A `WS /ws/{project_id}` 的连接层：
- 接受连接
- 发送 envelope-shaped greeting (ws.connected)
- 响应客户端 ping/pong 心跳

事件广播 (SPEC-11A WsEventEnvelope payload) deferred to Plan B。
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _envelope(event_type: str, project_id: str, payload: dict[str, Any]) -> str:
    """Shape per SPEC-11A WsEventEnvelope (subset used in this plan)."""
    return json.dumps({
        "type": event_type,
        "project_id": project_id,
        "timestamp": _now_iso(),
        "payload": payload,
    })


@router.websocket("/ws/{project_id}")
async def project_ws(websocket: WebSocket, project_id: str) -> None:
    await websocket.accept()
    await websocket.send_text(_envelope("ws.connected", project_id, {}))
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if msg.get("type") == "ping":
                await websocket.send_text(_envelope("pong", project_id, {}))
    except WebSocketDisconnect:
        return
```

- [ ] **Step 4: 在 main.py 注册 WS router**

```python
# src/backend/api/main.py 修改：
# import 列表追加：
from src.backend.api.routes import (
    cost,
    observability,
    preferences,
    projects,
    settings_bridge,
    system,
    tasks,
    websocket,  # 新增
)

# include_router 部分追加：
app.include_router(websocket.router)  # WS endpoint 自带 /ws/{project_id} 完整路径
```

- [ ] **Step 5: 跑 GREEN**

Run: `pytest tests/unit/backend/api/test_websocket_route.py -v`
Expected: 2 PASS。

- [ ] **Step 6: Commit**

```bash
git add src/backend/api/routes/websocket.py src/backend/api/main.py tests/unit/backend/api/test_websocket_route.py
git commit -m "[SPEC-INTEG-007] add WS /ws/{project_id} accept layer (broadcast deferred to Plan B)

Files Changed:
- src/backend/api/routes/websocket.py (new)
- src/backend/api/main.py (register ws router)
- tests/unit/backend/api/test_websocket_route.py (new, 2 cases)

Verification:
- pytest tests/unit/backend/api/test_websocket_route.py -v -> 2 PASS

Decisions:
- 仅实现 accept + greeting + ping/pong；事件广播 (SPEC-11A WsEventEnvelope payload + EventBus 桥接)
  deferred to Plan B（需要 in-process pubsub registry + WorkflowEngine sink hook，工作量超本 plan 范围）。
- envelope shape 已对齐 SPEC-11A WsEventEnvelope (type/project_id/timestamp/payload)，Plan B 直接复用。
- ws.connected 事件类型本 plan 自定义 (不在 SPEC-11A 17 个 EventType 中)，仅作连接确认；Plan B 视情况入册或移除。

Artifacts:
- WS /ws/{project_id} 端点暴露
- 前端 useProjects WS 连接不再失败"
```

---

### Task 8: 前端 vite.config.ts 加 server.proxy

**Files:**
- Modify: `src/frontend/vite.config.ts`

- [ ] **Step 1: 修改 vite.config.ts**

```typescript
// src/frontend/vite.config.ts 第 27 行替换：
  server: {
    port: 3000,
    host: "0.0.0.0",
    proxy: {
      "/api": {
        target: process.env.VITE_BACKEND_URL || "http://backend:8000",
        changeOrigin: true,
      },
      "/ws": {
        target: process.env.VITE_BACKEND_URL || "http://backend:8000",
        ws: true,
        changeOrigin: true,
      },
    },
  },
```

- [ ] **Step 2: 重启 frontend 容器**

```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System
docker compose -f docker-compose.dev.yml restart frontend
docker compose -f docker-compose.dev.yml logs --tail=30 frontend
```

Expected: vite restart，看到 `VITE v6.2.0 ready in ...ms`。

- [ ] **Step 3: 验证 proxy 工作**

Run: `curl -sS -o /tmp/api.out -w "HTTP %{http_code} type=%{content_type}\n" http://localhost:3000/api/projects && head -c 200 /tmp/api.out`
Expected: `HTTP 200 type=application/json` + body `{"projects":[]}`（空列表 OK，关键是 application/json 不是 text/html）。

- [ ] **Step 4: 验证 WS proxy（用 wscat 或 curl）**

Run: `curl -sS -o /tmp/ws.out -w "HTTP %{http_code}\n" -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" http://localhost:3000/ws/proj_test`
Expected: `HTTP 101`（WebSocket upgrade 成功）或 `HTTP 426`（如 vite 不主动 upgrade，但至少不是 404）。

- [ ] **Step 5: Commit**

```bash
git add src/frontend/vite.config.ts
git commit -m "[SPEC-INTEG-008] add vite server.proxy for /api and /ws routing to backend

Files Changed:
- src/frontend/vite.config.ts

Verification:
- curl http://localhost:3000/api/projects -> HTTP 200 application/json (not SPA HTML)
- WebSocket upgrade handshake to /ws/* succeeds

Decisions:
- target 用 http://backend:8000 (容器内服务名)，本地开发可通过 VITE_BACKEND_URL env 覆盖。
- ws: true 让 proxy 透传 WebSocket upgrade。

Artifacts:
- /api 和 /ws 在 dev 环境从 vite (3000) 透传到 backend (8000)"
```

---

### Task 9: 前端清除所有 `/api/v1/` 字面量 + 修正 WebSocket 路径

**Files:**
- Modify: `src/frontend/hooks/useProjects.ts:12`
- Modify: `src/frontend/hooks/useCreateProject.ts:10`
- Modify: `src/frontend/hooks/useProjectState.ts:8`
- Modify: `src/frontend/hooks/useEventStream.ts:12`
- Modify: `src/frontend/hooks/usePreferenceWriteback.ts:29,45`
- Modify: `src/frontend/hooks/useMasterAudioSubscription.ts:38`
- Modify: `src/frontend/components/CandidateSelector.tsx:22`
- Modify: `src/frontend/types/project.ts:1`
- Modify: `src/frontend/mocks/handlers.ts:11-18`
- Modify: `src/frontend/pages/ProjectList.tsx:8`

- [ ] **Step 1: 全文替换 `/api/v1/projects` → `/api/projects`**

执行：
```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System/src/frontend
grep -rl "api/v1/projects" --include="*.ts" --include="*.tsx" .
```
对返回的每个文件，把 `api/v1/projects` 替换为 `api/projects`：
- `hooks/useProjects.ts`
- `hooks/useCreateProject.ts`
- `hooks/useProjectState.ts`
- `hooks/useEventStream.ts`
- `hooks/usePreferenceWriteback.ts`（2 处）
- `components/CandidateSelector.tsx`
- `types/project.ts`（注释里）
- `mocks/handlers.ts`（5 处）

> 用 IDE 多文件替换或：`find . -type f \( -name "*.ts" -o -name "*.tsx" \) -not -path "./node_modules/*" -not -path "./dist/*" -exec sed -i '' 's|api/v1/projects|api/projects|g' {} \;`（macOS sed 形式）。**操作前先 git status 确认无未提交改动**。

- [ ] **Step 2: 修正 useMasterAudioSubscription.ts WS 路径**

```typescript
// src/frontend/hooks/useMasterAudioSubscription.ts 第 38 行替换：
      : `/ws/${projectId}`;  // 原 `/ws/projects/${projectId}`
```

- [ ] **Step 3: 修正 ProjectList.tsx WS URL（去掉 hardcode 8000、去掉 /projects）**

```typescript
// src/frontend/pages/ProjectList.tsx 第 8 行替换：
// 原: const { data, isLoading, isError } = useProjects("ws://localhost:8000/ws/projects")
// 改为：使用相对路径 + 浏览器 location 推导 ws/wss
function buildProjectsWsUrl(): string {
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  // 列表页订阅一个全局 channel id（约定为 "_all"），让 WS endpoint
  // 把所有项目的事件透传给列表页（Plan B 会按此 channel 实现 fan-out）。
  // 当前 plan WS endpoint 仅 accept 不广播，此 URL 仅保证连接成功。
  return `${proto}://${window.location.host}/ws/_all`;
}

export function ProjectList() {
  const { data, isLoading, isError } = useProjects(buildProjectsWsUrl());
  // ...剩余不变
}
```

> **注意**：`_all` 是约定标识符，对应 WS endpoint `project_id` 路径参数。本 plan WS endpoint 不区分 project_id（accept 后仅心跳），所以此约定不影响功能；Plan B 会接 fan-out 逻辑使用此约定。

- [ ] **Step 4: 跑前端单测**

Run: `cd src/frontend && pnpm test -- --run`
Expected: PASS（mocks/handlers.ts 已经统一更新）。

- [ ] **Step 5: 验证 grep 无 v1 残留**

Run: `cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System && grep -rn "api/v1" src/frontend --include="*.ts" --include="*.tsx" | grep -v "/dist/" | grep -v "node_modules"`
Expected: 无输出（如有，回到 Step 1 补漏）。

- [ ] **Step 6: Commit**

```bash
git add src/frontend/
git commit -m "[SPEC-INTEG-009] remove /api/v1/ prefix from frontend; align WS path to /ws/{project_id}

Files Changed:
- src/frontend/hooks/{useProjects,useCreateProject,useProjectState,useEventStream,usePreferenceWriteback,useMasterAudioSubscription}.ts
- src/frontend/components/CandidateSelector.tsx
- src/frontend/types/project.ts
- src/frontend/mocks/handlers.ts
- src/frontend/pages/ProjectList.tsx

Verification:
- grep -rn 'api/v1' src/frontend --include='*.ts' --include='*.tsx' | grep -v dist | grep -v node_modules -> empty
- pnpm --filter frontend test -- --run -> PASS

Decisions:
- WS URL 改为相对路径 + window.location 推导，去掉 hardcode localhost:8000，让 proxy 透传 (Task 8)。
- ProjectList 用约定 channel id '_all' 订阅所有项目事件；本 plan WS endpoint 不区分 project_id，
  Plan B 实现 fan-out 时按此约定 broadcast。

Artifacts:
- 前端全部 v1 字面量清除
- WS 路径符合 SPEC-1A /ws/{project_id} 形态"
```

---

### Task 10: E2E 浏览器集成验证

**Why**：HARNESS §4 + AGENTS.md 要求"业务完整交付门槛"——不能只有单测 PASS 就声明完成，必须真实浏览器验证。

**Files:** 无新建/修改，仅验证。

- [ ] **Step 1: 重启容器**

```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System
docker compose -f docker-compose.dev.yml restart
docker compose -f docker-compose.dev.yml logs --tail=30
```

Expected: backend `Application startup complete`，frontend `VITE v6.2.0 ready`。

- [ ] **Step 2: HTTP 烟测**

```bash
curl -sS http://localhost:3000/api/projects | head -c 200
curl -sS -o /dev/null -w "HTTP %{http_code}\n" http://localhost:3000/api/projects/proj_x/state
curl -sS http://localhost:3000/openapi.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d['paths']), 'paths')"
```

Expected:
- `{"projects":[]}` 或包含项目的 JSON
- 第二条 HTTP 404（项目不存在）
- paths 数量 ≥ 21（与 EXPECTED_PATHS_AFTER_PLAN_A 对齐）

- [ ] **Step 3: 浏览器打开 http://localhost:3000**

打开浏览器（用户手动），观察：
- ✅ ProjectList 标题显示"项目列表"
- ✅ "新建项目" 按钮可见
- ✅ 列表为空时显示空状态（不再"加载失败"）
- ✅ 浏览器 DevTools Network 标签：所有 /api/* 请求 HTTP 200
- ✅ DevTools Console 无红色 fetch error
- ✅ DevTools Network WS 标签：`/ws/_all` 连接 status 101 (Switching Protocols)，并收到 ws.connected envelope

- [ ] **Step 4: 创建项目流程**

- 点击"新建项目"
- 填入 title（任意） + description（≥ 10 字）
- 提交
- 期望：跳转到 PhaseDetail 页，URL 形如 `/projects/proj_xxxxxxxx/phases/0`，phases nav 显示 P0 高亮

- [ ] **Step 5: 列表回退查看**

- 浏览器返回到 `/projects`
- 期望：列表中出现刚创建的项目卡片，点击进入再次进 PhaseDetail

- [ ] **Step 6: 收集证据并 commit 验证记录到 PROGRESS.md**

```bash
git status  # 应为 clean
# 不需要 commit 代码，但 PROGRESS.md 已经记录前 9 个 task；
# 在 "Open follow-ups" 加一行：
# "Plan A E2E 验证 PASS @ 2026-04-26（curl + 浏览器）；Plan B/C/D 待启动"
git add PROGRESS.md
git commit -m "[SPEC-INTEG-010] Plan A E2E verification PASS

Files Changed:
- PROGRESS.md (Open follow-ups note)

Verification:
- curl /api/projects -> 200 application/json
- 浏览器 ProjectList 渲染，无加载失败
- WS /ws/_all 连接 101
- 创建项目 + 进入 PhaseDetail 流程通

Decisions:
- 业务完整交付门槛达成：浏览器能打开、能创建项目、能进入详情页。
- Plan A 边界外的功能 (advance/skip/rollback/chat 按钮) 点击会 404，符合 plan 预期。

Artifacts:
- E2E PASS 记录"
```

---

## Self-Review (writing-plans 强制)

### Spec Coverage（SPEC-A SPEC-1A 覆盖核对）

| SPEC-1A 端点 | 本 plan 覆盖 task | 状态 |
|---|---|---|
| GET /api/projects | T4 | ✅ |
| POST /api/projects | T4 (迁移) | ✅ |
| GET /api/projects/{id} | T5 | ✅ |
| DELETE /api/projects/{id} | — | ⏭️ Plan D |
| GET /api/projects/{id}/state | T6 | ✅ |
| POST /api/projects/{id}/advance | — | ⏭️ Plan D |
| POST /api/projects/{id}/skip | — | ⏭️ Plan D |
| POST /api/projects/{id}/rollback | — | ⏭️ Plan D |
| POST /api/projects/{id}/chat | — | ⏭️ Plan D |
| GET /api/projects/{id}/tasks | T2 (路径修复) | ✅ |
| POST /api/projects/{id}/tasks/{tid}/cancel | — | ⏭️ Plan D |
| GET /api/projects/{id}/preferences | T2 (路径修复) | ✅ |
| POST /api/projects/{id}/preferences/confirm | — | ⏭️ Plan D |
| GET /api/projects/{id}/phases/{p}/artifact | — | ⏭️ Plan D / SPEC-B |
| GET /api/projects/{id}/events | T2 (路径修复) | ✅ |
| GET /api/projects/{id}/costs | T2 (cost→costs) | ✅ |
| GET /api/system/status | T2 | ✅ |
| GET /api/settings (+ 6 个 settings 子端点) | 已对齐 | ✅ |
| WS /ws/{project_id} | T7 (accept 层) | ⚠️ 部分（广播 deferred Plan B） |

**结论**：SPEC-1A 已实现端点（11 个）100% 路径对齐；新增端点 4 个（GET 列表/详情/state、WS accept）；FSM 操作端点 7 个明确 deferred 到 Plan D。本 plan **scope 自洽**。

### Placeholder Scan

- ❌ 无 "TBD/TODO/implement later" 字样
- ❌ 无 "Add appropriate error handling" 类模糊指引
- ❌ 无 "Write tests for the above" 而无测试代码
- ❌ 无 "Similar to Task N" 简略
- ✅ 每个 step 均含真实代码块或可执行命令
- ⚠️ T2 Step 8 中 "对每个失败测试文件…改路径"——这是合理的，因 Step 1 已要求执行者先 ls 列出真实测试文件清单后再做（HARNESS §12 task 卡合规）

### Type Consistency

- 所有后端端点装饰器路径在 main.py prefix + router 装饰器组合后产生的 OpenAPI path 与 SPEC-1A 字面量一致（验证：T1 的快照测试守护此一致性）。
- `_row_to_project_dict` 的字段集 (project_id/title/description/current_phase/status/created_at/updated_at) 与 schema.sql `CREATE TABLE projects` 7 列完全对应。
- WS envelope shape `(type, project_id, timestamp, payload)` 对应 `src/shared/schemas/events.py:187 WsEventEnvelope`，Plan B 复用无歧义。

### 风险清单

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| `phases` 表实际列名与 T6 Step 2 假设不符（schema.sql `phase_num`/`status`/`artifact_path` 在 SPEC-A 标识为 `phase`/...） | 中 | 中 | T6 Step 1 强制读 schema.sql 拿真实列名，必要时调整测试与实现 |
| 现有 backend api 测试用例数量大、路径硬编码改动多 | 高 | 中 | T2 Step 1 先 ls 列清单；Step 8 系统化批量替换 |
| `app.dependency_overrides[projects.get_db]` 与现有其他 routes 的 `get_db()` 散落注入风格不一致 | 中 | 低 | 本 plan 不重构 db wiring，按现有风格添加；记录到 follow-up 待 SPEC-C 后续卡统一 |
| vite proxy `target: http://backend:8000` 在容器外（host）执行 `pnpm dev` 时不可达 | 低 | 低 | 用 `process.env.VITE_BACKEND_URL` 兜底；本项目 docker-compose.dev.yml 即容器内 dev，默认值合理 |
| WS endpoint accept 后无广播，前端 `useProjects` 的 invalidate 触发逻辑可能误以为"无事件" | 低 | 低 | 前端 react-query 仍有 staleTime=0 + manual refetch；Plan B 接入广播后自动恢复 |

---

## Follow-up Plans

按 Scope Check 拆分，本 plan 完成后产出以下 follow-up plans（每个独立可工作）：

### Plan B：SPEC-11A WebSocket 事件 payload 完整对齐

**Goal**：让 WS endpoint 真正广播 17 类事件 (PHASE_ENTERED / TASK_CREATED / ARTIFACT_PRODUCED / GATE_PASSED / PREFERENCE_EXTRACTED 等)，前端 useProjects 的 invalidate 触发链路打通。

**关键 task**：
- 创建 `src/backend/api/event_broadcaster.py` (in-process pubsub registry)
- 修改 WorkflowEngine sink wiring：写表后触发 broadcaster.broadcast()
- WS endpoint 在 accept 时注册到 broadcaster，断开移除
- 用 `tests/unit/backend/api/test_websocket_broadcast.py` 覆盖 17 类事件透传

**估时**：2-3 小时

### Plan C：SPEC-13A 错误码体系 + SPEC-13B 统一日志格式

**Goal**：所有 API 端点返回标准错误格式 `{error_code, message, details}` (17 codes)；所有日志走 `src/backend/core/observability.py` 输出 JSON 格式。

**关键 task**：
- 创建 `src/shared/constants/error_codes.py` (17 codes Enum)
- 创建 `src/backend/api/middleware/error_handler.py` (FastAPI exception handler)
- 修改各 routes 抛 `HTTPException` 改用 `APIError(error_code=...)`
- 配置 logging.config.dictConfig 输出 JSON
- 测试覆盖：每个错误码至少 1 个用例

**估时**：3-4 小时

### Plan D：SPEC-D Pipeline FSM 操作端点

**Goal**：实现 advance/skip/rollback/chat/cancel/preferences-confirm/artifact 7 个端点，前端按钮全部可工作。

**关键 task**（每个端点一组 RED-GREEN）：
- POST /api/projects/{id}/advance（接 phase_ops.advance_phase）
- POST /api/projects/{id}/skip（接 phase_ops.skip_phase）
- POST /api/projects/{id}/rollback（接 rollback_cascade）
- POST /api/projects/{id}/chat（接 intent_router）
- POST /api/projects/{id}/tasks/{tid}/cancel（接 task_ledger）
- POST /api/projects/{id}/preferences/confirm（接 preference_service）
- GET /api/projects/{id}/phases/{p}/artifact（静态文件 + 签名）
- DELETE /api/projects/{id}（软删除）

**估时**：6-10 小时

### Plan E（可选）：SPEC-0A.3 ProjectState 完整字段回填

**Goal**：让 GET /api/projects/{id}/state 返回 SPEC-0A.3 中的所有顶层字段（candidates/verification_records/preferences/style_lock 等）。

**前置**：Plan B + Plan C + Plan D（依赖 PreferenceService、Claim/VerificationRecord、artifact 服务）。

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-26-spec-a-api-alignment-and-frontend-integration.md`.

**两种执行方式**：

### 1. Subagent-Driven（推荐 — HARNESS §subagent-driven-development）

我（主 agent）每个 task 派一个 fresh subagent 执行，执行间做 code review checkpoint：
- 每个 task 一个独立 subagent（context 隔离）
- 每个 task 完成后我做两阶段 review（spec 合规 + 代码质量）
- 出现问题立即回滚到上个 commit，重派 subagent

**适用**：希望多任务长程稳定推进，且能容忍 review 间的等待。

### 2. Inline Execution（superpowers:executing-plans）

我在当前 session 内顺序执行 task，每完成 1-2 个 task 自我 verification + 报告：
- 上下文累积可能在后期影响判断
- 速度较快，反馈密集
- 适用：用户希望全程跟随、可随时打断微调

**适用**：希望节奏紧凑，每步即时跟进。

---

## 执行前最后确认事项

1. **commit prefix 编号约定**：本 plan 使用 `[SPEC-INTEG-001..010]` 前缀。如需改用既有 SPEC 编号（例如 `[SPEC-C-100..]` 或 `[SPEC-E-100..]`），执行前替换 plan 中所有 commit message 模板。
2. **git worktree**：按 HARNESS + `superpowers:using-git-worktrees`，建议在新 worktree（如 `feat/spec-integ-api-alignment`）执行此 plan。
3. **执行模式选择**：subagent-driven vs inline（参见上节）。

请回复：**「执行模式 + 编号约定 + worktree 名」**（例：「subagent-driven，沿用 SPEC-INTEG 编号，worktree=feat/api-integration-repair」），我即开始按 plan 执行。
