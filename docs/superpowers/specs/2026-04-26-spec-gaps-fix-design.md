# SPEC 错漏全量修复设计方案

> Date: 2026-04-26
> Source: `docs/PROBLEM_REPORT_SPEC_GAPS_2026-04-26.md`
> Authority: HARNESS.md v1.1.0
> Purpose: 为下一个 AI 提供可执行的 task card 编写依据,修复 PROD 全 SPEC 体系错漏

---

## 0. 修复目标

修复 PROBLEM_REPORT 中 P0/P1/P2 全部错漏项,使系统通过完整 docker compose 真实流水线验证。

### 成功定义

1. `pytest tests/` 全部通过
2. `vitest run` 全部通过
3. Route diff 脚本输出 missing=0, extra=0, double-prefix=0
4. `grep -rn '/api/v1/' src/frontend/` 返回空
5. `grep -rn 'EVID_' src/backend/api/` 返回 >0 条
6. `grep -rn 'proxy' src/frontend/vite.config.ts` 返回 proxy 配置
7. docker compose up 后: 创建项目 → 推进 12 阶段 → WS 收到业务事件 → 日志为 JSON Lines → 错误响应含 EVID_ code

### 修复原则

- **Contract-first**: 所有路由/事件/错误码从 `src/shared/contracts/` 定义出发
- **TDD 硬约束**: 先写失败测试,再写最小实现 (HARNESS.md §4)
- **Layer 依赖**: 严格遵循 HARNESS.md §2 依赖方向
- **照抄 `settings_bridge.py`**: 项目内唯一正确的 FastAPI prefix 写法
- **不信任 PROGRESS.md 的 "DONE"**: 所有实现以 SPEC 文本和真实代码对照为准

---

## 1. 修复阶段总览

```
Phase 1: 合约层修正 (Layer 0)         — 地基
Phase 2: 路由层修复 (P0 #1-4,7,9)    — API 通路正确
Phase 3: 前端层修复 (P0 #5-6)        — 前后端对接
Phase 4: WebSocket 广播 (P0 #8)      — 17 种事件触达前端
Phase 5: 集成层 (P1 #10-13,18-19)    — 流水线真实运转
Phase 6: 媒体渲染 (P1 #15-17)        — Remotion/Whisper/brand_kit
Phase 7: 长期一致性 (P2)             — 代码生成链/枚举同步/组件补全
```

每个 Phase 独立可验证,Phase 2-4 完成后系统端到端可跑通。

---

## 2. Phase 1: 合约层修正 (Layer 0)

### 目标

补齐 `src/shared/contracts/` 中缺失的 EventType、ErrorCode 枚举,使其成为真正的 single source of truth。

### 新增文件

#### 2.1 `src/shared/contracts/event_types.py`

17 种 WebSocket 事件类型枚举 (来源: SPEC-11A):

- `phase.entered`, `phase.completed`, `phase.failed`
- `task.created`, `task.assigned`, `task.running`, `task.completed`, `task.failed`
- `review.requested`, `review.completed`
- `artifact.generated`, `artifact.updated`
- `error.occurred`
- `project.created`, `project.updated`, `project.deleted`
- `preference.updated`
- `ws.connected`, `ws.disconnected`
- `heartbeat`

#### 2.2 `src/shared/contracts/event_types.ts`

同上,TypeScript 版本,供前端 `types/events.ts` 导入。

#### 2.3 `src/shared/contracts/error_codes.py`

17 个 EVID_ 错误码 → HTTP status code → 用户消息映射表:

- EVID_1001..EVID_1017 映射到 400/404/409/422/500/503
- 暴露 `lookup_evid(evid_code: str) -> dict` 函数

#### 2.4 `src/shared/contracts/error_codes.ts`

同上,TypeScript 版本,供前端 `utils/errorUxMap.ts` 导入。

### 现有文件 (不变)

- `src/shared/contracts/api_routes.py` — 已与 SPEC-1A 一致,不变
- `src/shared/contracts/api_routes.ts` — 同步检查,如有偏差则更新

### TDD

对每个新增合约文件:
1. 写 schema 验证测试 (枚举值完整、映射表无缺漏)
2. 写实现
3. 写跨语言一致性测试 (Python enum ↔ TypeScript const 项数一致)

---

## 3. Phase 2: 路由层修复 (P0 #1-4, #7, #9)

### 核心原则

**统一写法**: 所有 router 必须使用 `APIRouter(prefix="/api/xxx")` + **相对路径**装饰器。禁止在装饰器内写绝对路径。

参考模板 (来自 `settings_bridge.py`):
```python
router = APIRouter(prefix="/api/settings", tags=["settings"])

@router.get("")           # → /api/settings
@router.put("/model-config")  # → /api/settings/model-config
```

### 2.1 `routes/system.py` 修复

**当前问题**: `router = APIRouter()` + `@router.get("/api/system/status")` + `main.py` mount `prefix="/api/system"` → 实际路径 `/api/system/api/system/status`

**修复后**:
```python
router = APIRouter(prefix="/api/system", tags=["system"])

@router.get("/status")  # → /api/system/status
```

**移除** `POST /api/projects` (移到 `projects.py`)。

### 2.2 `routes/observability.py` 修复

**当前问题**: `main.py` mount `prefix="/api/observability"` + 装饰器 `@router.get("/api/projects/{id}/events")` → 实际路径 `/api/observability/api/projects/{id}/events`。且 `/api/observability` 前缀本身违 SPEC-A。

**修复后**:
```python
router = APIRouter(prefix="/api", tags=["observability"])

@router.get("/observability/status")
@router.get("/projects/{project_id}/events")
@router.get("/projects/{project_id}/audit")
@router.get("/projects/{project_id}/artifacts")
```

`main.py` 中挂载: `app.include_router(observability.router)` (无额外 prefix)。

### 2.3 `routes/cost.py` 修复

**当前问题**: 双叠 + `cost` 单数 (SPEC 为 `costs`)。

**修复后**:
```python
router = APIRouter(prefix="/api", tags=["cost"])

@router.get("/projects/{project_id}/costs")
```

### 2.4 新建 `routes/projects.py`

从 `system.py` 移出 `POST /api/projects`,并补全 SPEC-1A 要求的 projects CRUD:

```python
router = APIRouter(prefix="/api/projects", tags=["projects"])

@router.get("")            # GET /api/projects (列表)
@router.post("")           # POST /api/projects (创建)
@router.get("/{id}")       # GET /api/projects/{id} (详情)
@router.get("/{id}/state") # GET /api/projects/{id}/state (已实现则保留)
```

### 2.5 `routes/tasks.py` 修复

**修复后**:
```python
router = APIRouter(prefix="/api", tags=["tasks"])

@router.get("/projects/{project_id}/tasks")
```

### 2.6 `routes/preferences.py` 修复

**修复后**:
```python
router = APIRouter(prefix="/api", tags=["preferences"])

@router.get("/projects/{project_id}/preferences")
```

### 2.7 `main.py` 更新

```python
app.include_router(system.router)           # prefix 已在 router 内
app.include_router(projects.router)         # prefix 已在 router 内
app.include_router(tasks.router)            # 无额外 prefix
app.include_router(preferences.router)      # 无额外 prefix
app.include_router(observability.router)    # 无额外 prefix
app.include_router(cost.router)             # 无额外 prefix
app.include_router(settings_bridge.router)  # 不变
app.include_router(websocket.router)        # 不变
```

### 2.8 新增 `api/middleware/error_handler.py` (P0 #7)

统一异常处理中间件,拦截所有 `HTTPException` 和未处理异常:

```python
from starlette.requests import Request
from starlette.responses import JSONResponse
from src.shared.contracts.error_codes import lookup_evid

async def evid_error_handler(request: Request, exc: Exception) -> JSONResponse:
    ...
    return JSONResponse(
        status_code=status,
        content={"error": {"code": evid_code, "message": msg, "details": details}}
    )
```

在 `main.py` 中注册:
```python
app.add_exception_handler(HTTPException, evid_error_handler)
app.add_exception_handler(Exception, evid_error_handler)
```

### 2.9 `main.py` JSON 日志初始化 (P0 #9)

```python
import logging
from src.backend.core.logging import JsonLineFormatter

handler = logging.StreamHandler()
handler.setFormatter(JsonLineFormatter())
logging.getLogger().handlers = [handler]
logging.getLogger().setLevel(logging.INFO)
```

### 路由层验证命令

```bash
python3 -c "
from src.backend.api.main import app
from src.shared.contracts.api_routes import API_ROUTES
import re
def norm(p): return re.sub(r'\{[^}]+\}', '{}', p)
actual = {(m, norm(r.path)) for r in app.routes if hasattr(r,'methods') for m in r.methods if m not in {'HEAD','OPTIONS'}}
expected = {(r['method'], norm(r['path'])) for r in API_ROUTES if r['type']=='rest'}
missing = expected - actual
extra = actual - expected
double = [p for _,p in actual if '/api/' in p[5:]]
print(f'missing: {len(missing)} {missing}')
print(f'extra: {len(extra)} {extra}')
print(f'double-prefix: {len(double)} {double}')
assert len(missing) == 0, f'missing routes: {missing}'
assert len(extra) == 0, f'extra routes: {extra}'
assert len(double) == 0, f'double-prefix routes: {double}'
print('ALL ROUTE CHECKS PASSED')
"
```

---

## 4. Phase 3: 前端层修复 (P0 #5-6)

### 4.1 删除 `/api/v1/` 前缀

| 文件 | 行 | 改动 |
|------|-----|------|
| `hooks/useProjects.ts:12` | `/api/v1/projects` | `/api/projects` |
| `components/CandidateSelector.tsx:22` | `/api/v1/projects/${id}/preferences/confirm` | `/api/projects/${id}/preferences/confirm` |
| `mocks/handlers.ts:11-18` | 全部 `*/api/v1/` | `*/api/` |
| `types/project.ts:1` | 注释 `GET /api/v1/projects` | `GET /api/projects` |
| 其他引用 | 全局搜索 | 全部替换 |

### 4.2 `vite.config.ts` 添加 proxy

```ts
server: {
  port: 3000,
  host: "0.0.0.0",
  proxy: {
    "/api": "http://localhost:8000",
    "/ws": { target: "ws://localhost:8000", ws: true },
  },
},
```

### 4.3 `types/events.ts` 同步 EventType 枚举

```ts
import type { EventType } from "@shared/contracts/event_types";
export type { EventType };
```

消除组件中的魔法字符串 `"phase.entered"`。

### 前端验证命令

```bash
grep -rn '/api/v1/' src/frontend/ | wc -l  # 期望 0
grep -rn 'proxy' src/frontend/vite.config.ts  # 期望返回 proxy 配置
cd src/frontend && npx tsc --noEmit
cd src/frontend && npx vitest run
```

---

## 5. Phase 4: WebSocket 事件广播 (P0 #8)

### 目标

让 SPEC-11A 声明的 17 种事件能通过 WS 通道到达前端。

### 改动: `routes/websocket.py`

当前 50 行只实现 ping/pong。扩展为:

1. **连接池管理**
```python
class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, set[WebSocket]] = {}
    async def connect(self, project_id: str, ws: WebSocket): ...
    async def disconnect(self, project_id: str, ws: WebSocket): ...
    async def broadcast(self, project_id: str, event_type: str, payload: dict): ...
```

2. **暴露 broadcast 给其他模块**
```python
manager = ConnectionManager()
```

3. **pipeline/dispatcher 调用 broadcast**
各个 phase worker 在状态转换后调用:
```python
from src.backend.api.routes.websocket import manager
await manager.broadcast(project_id, "phase.advanced", { ... })
```

**注意**: 需要解决循环依赖。`routes/websocket.py` 不应被 `engine/` import。采用事件回调注入模式:
```python
# main.py 启动时
from src.backend.core.event_bus import set_broadcast_handler
from src.backend.api.routes.websocket import manager
set_broadcast_handler(manager.broadcast)
```

### WebSocket 验证命令

```bash
# 集成测试: 连接 WS → 模拟 phase advance → 断言收到 phase.advanced
pytest tests/integration/test_ws_broadcast.py -v
```

---

## 6. Phase 5: 集成层 (P1)

### 6.1 Pre-flight 真实检查器 (P1 #10)

`core/preflight.py:60-64` 当前 9 个检查器全是 `_stub_ok()`:

| 检查器 | 实现 |
|--------|------|
| `check_llm` | 真实 ping LiteLLM (轻量 completion, 1 token) |
| `check_tts` | 真实 ping TTS provider |
| `check_sqlite` | `SELECT 1` + 写测试 |
| `check_disk` | `shutil.disk_usage` ≥ 100MB |
| 其余 5 个可降级检查器 | 保留 stub,但记录 WARN |

### 6.2 hard claims 验证阻断 (P1 #12)

`gates/gate_p8.py, gate_p10.py, gate_p11.py`:
```python
def check_hard_claims(db: Connection, project_id: str) -> list[str]:
    rows = db.execute(
        "SELECT claim_id FROM claims WHERE project_id = ? AND verification_status != 'verified'",
        (project_id,)
    ).fetchall()
    if rows:
        return [f"unverified claim: {r['claim_id']}" for r in rows]
    return []
```

### 6.3 gate_registry / phase_registry 显式绑定 (P1 #13)

`gates/__init__.py`:
```python
from src.backend.gates.gate_registry import gate_registry
from src.backend.gates.gate_p0 import GateP0
# ... 全部 12 个 gate

for i, gate_cls in enumerate([GateP0, GateP1, ..., GateP11]):
    gate_registry.register(i, gate_cls)
```

### 6.4 TaskType docstring 修复 (P1 #14)

`engine/task_types.py`: 移除 "8 canonical types" → 改为 "17 task types"。

### 6.5 agent_call_log + redact hook (P1 #18)

`services/llm_service.py`:
```python
def _log_and_redact(db, agent_name, duration_ms, tokens, cost, project_id):
    from src.backend.core.redaction import redact_text
    db.execute(
        "INSERT INTO agent_call_log (...) VALUES (...)",
        [redact_text(p) if isinstance(p, str) else p for p in params]
    )
```

### 6.6 SQLite 备份 (P1 #19)

新增 `scripts/backup_sqlite.py`:
```python
import shutil
from pathlib import Path
db = Path("data/db/dev.sqlite3")
bak = Path("data/db/app.sqlite3.bak")
shutil.copy2(db, bak)
```

在 `workers/huey_config.py` 启动时调用;在 `phase_ops.py` advance 前调用。

---

## 7. Phase 6: 媒体渲染 (P1 #15-17)

### 7.1 brand_kit_overlay 真实 Remotion Sequence (P1 #15)

`services/brand_kit_overlay.py`: stub → 真实实现:
- Intro sequence: AbsoluteFill + brand logo fade-in
- Outro sequence: AbsoluteFill + watermark fade-out
- Watermark overlay during main content

### 7.2 Whisper 强制对齐 (P1 #16)

`services/subtitle_generator.py`: 均分 stub → Whisper API:
- 调用 Whisper `word_timestamps=True`
- 断言 `abs(word_start - expected) < 200ms`
- fallback: 如果 Whisper 不可用,使用 aeneas 强制对齐

### 7.3 voice_direction 映射表对齐 (P1 #17)

`services/voice_direction_bridge.py:22-32`:
```python
# 修复前
SPEED_MAP = {"slow": 0.8, "normal": 1.0, "fast": 1.2}

# 修复后
SPEED_MAP = {
    "much_slower": 0.7,
    "slightly_slower": 0.9,
    "normal": 1.0,
    "slightly_faster": 1.1,
    "much_faster": 1.3,
}
```

---

## 8. Phase 7: 长期一致性 (P2)

### 8.1 合约生成链

- `scripts/generate_routes_sdk.py`: 读取 `api_routes.py` → 生成 `api/routes_sdk.py` (类型安全 client)
- `scripts/generate_routes_sdk.ts`: 读取 `api_routes.ts` → 生成前端 `api/routesSdk.ts`
- 禁止手改 `/api/` 字面量,只允许 import 生成的 SDK

### 8.2 枚举同步

- `scripts/generate_event_types.py`: 从 SPEC-11A 生成 `event_types.py` + `event_types.ts`
- `scripts/generate_error_codes.py`: 从 SPEC-13A 生成 `error_codes.py` + `error_codes.ts`
- HARNESS.md §5.3 增加: "EventType/ErrorCode/TaskType 禁止手改,必须从 SPEC 生成"

### 8.3 覆盖率脚本

`scripts/check_spec_coverage.py`:
- 12 Phase × 4 维度 (Producer/Reviewer/Gate/Worker) 自动检查
- 输出缺失项列表,CI 中非零退出

### 8.4 前端组件补全

- 12 个 Phase preview 组件 (当前仅 P5 确认存在)
- `utils/errorUxMap.ts`: 17 个 EVID_ → 用户友好文案映射
- `components/ErrorState.tsx`: 使用 ERROR_UX_MAP 渲染错误

### 8.5 Remotion 真实接入

- `remotion/PreviewComposition.tsx`: 44 行 div wrapper → 真实 `<Composition>` + `renderMedia()`

---

## 9. TDD 策略 (每 Phase 遵守)

```
每个修复项的 RED-GREEN-REFACTOR 循环:

1. RED:     写失败测试 — 测试当前错误行为,确认测试因正确原因失败
2. GREEN:   写最小实现 — 让测试通过
3. REFACTOR: 清理 — 保持测试绿灯,改进结构
4. COMMIT:  git commit [SPEC-GAPFIX] <描述>
```

### TDD 例外 (HARNESS.md §4.3)

- `vite.config.ts` proxy 配置 — 配置修改,无需 TDD
- JSON 日志 handler 注册 — 配置修改
- TaskType docstring — 文档性改动

### 测试必须验证充分条件

HARNESS.md §4.2 规则 5: "Would a stub pass this test?"
- 路由测试必须 import `main:app` 并通过 TestClient 发请求,检查 `response.json()` 和 `status_code`
- WS 测试必须 `websocket.connect("/ws/...")` 并发 `send_text(json.dumps({"type":"ping"}))`,检查 `receive_text()` 包含 `pong`
- EVID 中间件测试必须触发真实 HTTPException,检查响应体 `error.code` 为 EVID_ 格式

---

## 10. 端到端验证 (最终检查)

```bash
# 1. 启动完整环境
docker compose up -d

# 2. 健康检查
curl http://localhost:8000/health

# 3. 路由对齐验证
python3 -c "
from src.backend.api.main import app
from src.shared.contracts.api_routes import API_ROUTES
import re
def norm(p): return re.sub(r'\{[^}]+\}', '{}', p)
actual = {(m, norm(r.path)) for r in app.routes if hasattr(r,'methods') for m in r.methods if m not in {'HEAD','OPTIONS'}}
expected = {(r['method'], norm(r['path'])) for r in API_ROUTES if r['type']=='rest'}
missing = expected - actual
extra = actual - expected
double = [p for _,p in actual if '/api/' in p[5:]]
assert len(missing) == 0, f'MISSING: {missing}'
assert len(extra) == 0, f'EXTRA: {extra}'
assert len(double) == 0, f'DOUBLE-PREFIX: {double}'
print('ROUTES: OK')
"

# 4. EVID_ 检查
grep -rn 'EVID_' src/backend/api/ | wc -l  # 期望 >0

# 5. 前端 /api/v1/ 残留检查
grep -rn '/api/v1/' src/frontend/  # 期望空

# 6. JSON 日志检查
curl -s http://localhost:8000/health | head -1  # 期望 {"ts":"...",...}

# 7. 真实流水线: 创建项目 → advance → 检查 WS 事件
# (手动或 e2e 脚本)

# 8. 全量测试
pytest tests/ -x --timeout=30
cd src/frontend && npx vitest run

# 9. 清理
docker compose down
```

---

## 11. Task Card 编写指南

下一个 AI 应为本方案每个改动项编写符合 HARNESS.md §12 格式的 task card:

```yaml
task_id: SPEC-GAPFIX-NNN
title: <Phase> - <简短描述>
spec_ref: PROBLEM_REPORT §2.X
allowed_files: [精确的文件列表]
forbidden_files: [HARNESS.md, CLAUDE.md, docs/specs/]
depends_on: [前置 task ID]
verification_commands: [具体命令]
completion_definition: [完成标准]
acceptance_criteria: [对应测试文件]
```

### 建议的 task card 粒度

Phase 1 (4 cards): event_types 合约 / error_codes 合约 / contracts 测试 / 跨语言一致性
Phase 2 (7 cards): system.py / observability.py / cost.py / projects.py (新) / tasks.py / preferences.py / main.py + middleware
Phase 3 (4 cards): 删除 /api/v1/ / vite proxy / types/events 同步 / apiClient 重构
Phase 4 (2 cards): ConnectionManager / event_bus 回调注入
Phase 5 (6 cards): preflight / claims 验证 / gate_registry / task_types docstring / agent_call_log / backup
Phase 6 (3 cards): brand_kit / Whisper / voice_direction
Phase 7 (5 cards): routes SDK 生成 / 枚举同步 / 覆盖率脚本 / 组件补全 / Remotion 接入

**约 31 张 task card,每张预计 2-5 分钟粒度。**

---

## 12. 关键风险

| 风险 | 缓解 |
|------|------|
| Phase 4 WS 事件广播可能涉及 cycle import | 使用 event_bus 回调注入模式,广播函数作为回调注册到 event_bus |
| Phase 6 Whisper API token 权限不足 (已知) | 先写测试 + 接口抽象,stub 实现保留,待 token 就绪后切换 |
| P2 生成链可能引入新 bug | 生成脚本先只读输出供人工审查,确认无误后再替换手写文件 |
| docker compose 启动失败缺少依赖 | Phase 1 前先跑 `docker compose up` 验证当前环境 |

---

(文档完)
