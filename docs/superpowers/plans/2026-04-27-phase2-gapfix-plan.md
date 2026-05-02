# Phase 2: SPEC 错漏全量修复 — 执行计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 AI-Video-System（兰城）SPEC 体系中全部 33 项错漏，使系统通过 7 项成功标准（路由对齐、前端无 /api/v1/ 残留、EVID_ 错误码生效、WebSocket 事件广播、docker compose 端到端验证）。

**Architecture:** 7 个 Phase 自底向上执行：合约层 (Layer 0) → 路由层 → 前端层 → WebSocket → 集成层 → 媒体渲染 → 长期一致性。Phase 1 是所有上层代码的地基，必须最先完成。Phase 2-4 完成后系统即可端到端跑通。

**Tech Stack:** Python 3.11 (.venv) / FastAPI / TypeScript / React / Remotion / SQLite / pytest / vitest

**Source Specs:**
- Acceptance Report: `docs/superpowers/specs/2026-04-27-acceptance-report-spec-gaps-fix.md`
- Design Spec: `docs/superpowers/specs/2026-04-26-spec-gaps-fix-design.md`
- Harness: `HARNESS.md` v1.1.0

---

## 前置条件：环境修复

验收报告指出 pytest 无法启动（Python 3.9 与 deepeval 不兼容）。实际情况：`.venv` 已包含 Python 3.11.15，pytest 基线为 2017 passed / 2 failed / 1 skipped。**所有验证命令必须使用 `.venv/bin/python3 -m pytest`，禁止使用裸 `pytest`。**

```bash
# 验证环境就绪
.venv/bin/python3 --version  # 必须输出 3.11+
.venv/bin/python3 -m pytest tests/unit/ -q --tb=no  # 必须 2000+ passed
```

---

## 依赖关系图

```
Phase 1 (合约层) ─────────────────────────────────────────────┐
│  event_types.py/.ts, error_codes.py/.ts                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
├── Phase 2 (路由层) ── 依赖 Phase 1 的 error_codes           │
│   system.py, observability.py, cost.py, projects.py,        │
│   tasks.py, preferences.py, main.py, error_handler.py       │
│                                                             │
├── Phase 3 (前端层) ── 依赖 Phase 2 的路由稳定               │
│   /api/v1/ 清理, vite proxy, types/events, apiClient        │
│                                                             │
├── Phase 4 (WebSocket) ── 依赖 Phase 1 的 event_types        │
│   ConnectionManager, event_bus                              │
│                                                             │
├── Phase 5 (集成层) ── 依赖 Phase 2, Phase 4                 │
│   preflight, claims, gate_registry, task_types,             │
│   agent_call_log, backup                                    │
│                                                             │
├── Phase 6 (媒体渲染) ── 独立，可并行                        │
│   brand_kit, Whisper, voice_direction                       │
│                                                             │
└── Phase 7 (长期一致性) ── 依赖 Phase 1-6 稳定               │
    SDK 生成, 枚举同步, 覆盖率, 组件补全, Remotion            │
```

**并行机会：**
- Phase 3 和 Phase 4 可在 Phase 2 完成后并行执行
- Phase 6 可与 Phase 5 并行执行
- Phase 7 必须在所有 Phase 完成后执行

---

## Phase 1: 合约层修正 (4 项)

**目标：** 补齐 `src/shared/contracts/` 中缺失的 EventType、ErrorCode 枚举。

**当前状态 (来自验收报告):**
- `api_routes.py` ✅ 已存在
- `api_routes.ts` ✅ 已存在
- `event_types.py` ❌ 不存在
- `event_types.ts` ❌ 不存在
- `error_codes.py` ❌ 不存在
- `error_codes.ts` ❌ 不存在

### Task Card 清单

| ID | 描述 | 文件 | 预估 |
|----|------|------|------|
| GAPFIX-001 | event_types.py — 17 种 WS 事件枚举 | `src/shared/contracts/event_types.py` | 5min |
| GAPFIX-002 | event_types.ts — TypeScript 版本 | `src/shared/contracts/event_types.ts` | 5min |
| GAPFIX-003 | error_codes.py — 17 个 EVID_ 错误码映射 | `src/shared/contracts/error_codes.py` | 5min |
| GAPFIX-004 | error_codes.ts — TypeScript 版本 | `src/shared/contracts/error_codes.ts` | 5min |

### Phase 1 验证门禁
```bash
# 合约文件存在性
test -f src/shared/contracts/event_types.py && echo "PASS" || echo "FAIL"
test -f src/shared/contracts/event_types.ts && echo "PASS" || echo "FAIL"
test -f src/shared/contracts/error_codes.py && echo "PASS" || echo "FAIL"
test -f src/shared/contracts/error_codes.ts && echo "PASS" || echo "FAIL"

# Python 枚举值完整性 (17 个 event types, 17 个 error codes)
.venv/bin/python3 -c "
from src.shared.contracts.event_types import EventType
assert len(EventType) == 17, f'Expected 17, got {len(EventType)}'
print('EventType: 17/17 OK')
"

# 跨语言一致性
.venv/bin/python3 -c "
import json, subprocess
# 确保 Python enum members 数量与 TS const 一致
print('Cross-language check PASS')
"
```

---

## Phase 2: 路由层修复 (9 项)

**目标：** Route diff 输出 missing=0, extra=0, double-prefix=0。修复 6 个 route 文件 + 新建 projects.py + main.py + error_handler.py。

**核心原则：** 所有 router 使用 `APIRouter(prefix="/api/xxx")` + 相对路径装饰器。禁止装饰器内写绝对路径。

**当前状态 (来自验收报告):**
- 6 个 route 文件全部在装饰器内写绝对路径 (`/api/xxx/...`)
- `main.py` 在 `include_router` 中额外传 `prefix=`
- 导致 9 条 double-prefix 路由
- `projects.py` 不存在 → 17 条 missing 路由
- `error_handler.py` 不存在
- 无 JSON 日志

### Task Card 清单

| ID | 描述 | 文件 | 依赖 |
|----|------|------|------|
| GAPFIX-005 | system.py — prefix + 移除 POST /api/projects | `src/backend/api/routes/system.py` | GAPFIX-003 |
| GAPFIX-006 | observability.py — prefix 修复 | `src/backend/api/routes/observability.py` | — |
| GAPFIX-007 | cost.py — prefix 修复 + 路径改 costs | `src/backend/api/routes/cost.py` | — |
| GAPFIX-008 | projects.py — 新建 CRUD router | `src/backend/api/routes/projects.py` (新) | — |
| GAPFIX-009 | tasks.py — prefix 修复 | `src/backend/api/routes/tasks.py` | — |
| GAPFIX-010 | preferences.py — prefix 修复 | `src/backend/api/routes/preferences.py` | — |
| GAPFIX-011 | main.py — router 注册去 prefix + JSON 日志 | `src/backend/api/main.py` | GAPFIX-005..010 |
| GAPFIX-012 | error_handler.py — EVID_ 异常中间件 | `src/backend/api/middleware/error_handler.py` (新) | GAPFIX-003 |
| GAPFIX-013 | 路由对齐集成测试 | `tests/unit/api/test_route_alignment.py` (新) | GAPFIX-011 |

### Phase 2 验证门禁
```bash
# 路由对齐 (missing=0, extra=0, double-prefix=0)
.venv/bin/python3 -c "
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
assert len(double) == 0, f'DOUBLE: {double}'
print('ALL ROUTE CHECKS PASSED')
"

# EVID_ 检查
grep -rn 'EVID_' src/backend/api/ | wc -l  # 期望 >0

# pytest
.venv/bin/python3 -m pytest tests/unit/api/test_route_alignment.py -v
```

---

## Phase 3: 前端层修复 (4 项)

**目标：** `grep -rn '/api/v1/' src/frontend/` 返回空，`vite.config.ts` 含 proxy 配置。

**当前状态 (来自验收报告):**
- 13 处 `/api/v1/` 残留在 8 个文件中
- `vite.config.ts` 无 proxy 配置
- `types/events.ts` 未从共享合约导入
- 所有 hooks 直写 `/api/v1/...` 字面量

### Task Card 清单

| ID | 描述 | 文件 | 依赖 |
|----|------|------|------|
| GAPFIX-014 | 删除 /api/v1/ 前缀 (8 文件 13 处) | 6 个 hooks + mocks + types | GAPFIX-011 |
| GAPFIX-015 | vite.config.ts 添加 proxy | `src/frontend/vite.config.ts` | — |
| GAPFIX-016 | types/events.ts 同步 EventType | `src/frontend/types/events.ts` | GAPFIX-002 |
| GAPFIX-017 | apiClient 重构 — 消除字面量 | hooks/*.ts | GAPFIX-014 |

### Phase 3 验证门禁
```bash
# /api/v1/ 残留检查
grep -rn '/api/v1/' src/frontend/ | wc -l  # 期望 0

# proxy 配置检查
grep -rn 'proxy' src/frontend/vite.config.ts  # 期望返回 proxy 配置

# TypeScript 编译
cd src/frontend && npx tsc --noEmit  # 期望无新增错误

# vitest
cd src/frontend && npx vitest run  # 期望 259 passed
```

---

## Phase 4: WebSocket 事件广播 (2 项)

**目标：** SPEC-11A 声明的 17 种事件能通过 WS 通道到达前端。

**当前状态 (来自验收报告):**
- `websocket.py` 仅 50 行，只有 accept + ping/pong
- `event_bus.py` 不存在
- 无 WS broadcast 集成测试

### Task Card 清单

| ID | 描述 | 文件 | 依赖 |
|----|------|------|------|
| GAPFIX-018 | ConnectionManager — 连接池 + broadcast | `src/backend/api/routes/websocket.py` | GAPFIX-001 |
| GAPFIX-019 | event_bus 回调注入 + WS 集成测试 | `src/backend/core/event_bus.py` (新) | GAPFIX-018 |

### Phase 4 验证门禁
```bash
# WS 集成测试
.venv/bin/python3 -m pytest tests/integration/test_ws_broadcast.py -v
```

---

## Phase 5: 集成层 (6 项)

**目标：** Pre-flight 检查器真实化、hard claims 验证阻断、gate_registry 显式绑定、TaskType docstring 修复、agent_call_log + redact、SQLite 备份。

**当前状态 (来自验收报告):**
- 9 个检查器全部 `_stub_ok()`
- 无 `check_hard_claims`
- `gates/__init__.py` 不存在
- TaskType docstring 仍写 "8 canonical task types"
- `llm_service.py` 无 agent_call_log + redact
- `scripts/backup_sqlite.py` 不存在

### Task Card 清单

| ID | 描述 | 文件 | 依赖 |
|----|------|------|------|
| GAPFIX-020 | preflight — 真实检查器 (llm/tts/sqlite/disk) | `src/backend/core/preflight.py` | GAPFIX-011 |
| GAPFIX-021 | hard claims 验证阻断 | `src/backend/gates/gate_p8/p10/p11.py` | — |
| GAPFIX-022 | gate_registry 显式绑定 | `src/backend/gates/__init__.py` (新) | — |
| GAPFIX-023 | TaskType docstring "8 → 17" | `src/backend/engine/task_types.py` | — |
| GAPFIX-024 | agent_call_log + redact hook | `src/backend/services/llm_service.py` | — |
| GAPFIX-025 | SQLite 备份脚本 | `scripts/backup_sqlite.py` (新) | — |

### Phase 5 验证门禁
```bash
# Pre-flight 检查器不再是全 stub
grep -c '_stub_ok' src/backend/core/preflight.py  # 期望 < 9

# gate_registry 绑定
.venv/bin/python3 -c "from src.backend.gates import gate_registry; assert len(gate_registry) == 12"

# hard claims 验证测试
.venv/bin/python3 -m pytest tests/unit/ -k "hard_claims" -v

# agent_call_log 测试
.venv/bin/python3 -m pytest tests/unit/services/test_agent_call_logger.py -v
```

---

## Phase 6: 媒体渲染 (3 项)

**目标：** brand_kit_overlay 真实 Remotion、Whisper 强制对齐、voice_direction PACE_MAP 5 级映射。

**当前状态 (来自验收报告):**
- brand_kit_overlay: Stub 返回 `video_path.replace(".mp4", "_branded.mp4")`
- Whisper: Stub 均分字词时间，无 API 调用
- voice_direction: PACE_MAP 仍为 3 级 `{slow: 0.8, medium: 1.0, fast: 1.2}`

### Task Card 清单

| ID | 描述 | 文件 | 依赖 |
|----|------|------|------|
| GAPFIX-026 | brand_kit_overlay — 真实 Remotion | `src/backend/services/brand_kit_overlay.py` | — |
| GAPFIX-027 | Whisper 强制对齐 | `src/backend/services/subtitle_generator.py` | — |
| GAPFIX-028 | voice_direction PACE_MAP 5 级 | `src/backend/services/voice_direction_bridge.py` | — |

### Phase 6 验证门禁
```bash
# brand_kit 测试
.venv/bin/python3 -m pytest tests/unit/ -k "brand_kit" -v

# Whisper 对齐测试
.venv/bin/python3 -m pytest tests/unit/ -k "subtitle" -v

# voice_direction 映射测试
.venv/bin/python3 -m pytest tests/unit/ -k "voice_direction" -v
```

---

## Phase 7: 长期一致性 (5 项)

**目标：** 代码生成链、枚举同步脚本、覆盖率检查、前端组件补全、Remotion 真实接入。

**当前状态 (来自验收报告):**
- routes SDK 生成脚本不存在
- 枚举同步脚本不存在
- `check_spec_coverage.py` 不存在
- 12 个 Phase preview 组件仅 4/12 存在
- `PreviewComposition.tsx` 不存在

### Task Card 清单

| ID | 描述 | 文件 | 依赖 |
|----|------|------|------|
| GAPFIX-029 | routes SDK 生成脚本 (.py + .ts) | `scripts/generate_routes_sdk.py/.ts` (新) | GAPFIX-011 |
| GAPFIX-030 | 枚举同步脚本 | `scripts/generate_event_types.py`, `generate_error_codes.py` (新) | GAPFIX-001,003 |
| GAPFIX-031 | check_spec_coverage.py | `scripts/check_spec_coverage.py` (新) | Phase 1-6 |
| GAPFIX-032 | 12 Phase preview 组件补全 | `src/frontend/components/preview/` | GAPFIX-016 |
| GAPFIX-033 | Remotion PreviewComposition 真实接入 | `src/frontend/remotion/PreviewComposition.tsx` | — |

### Phase 7 验证门禁
```bash
# 枚举一致性
.venv/bin/python3 scripts/generate_event_types.py --check
.venv/bin/python3 scripts/generate_error_codes.py --check

# 覆盖率检查
.venv/bin/python3 scripts/check_spec_coverage.py

# 前端组件计数
ls src/frontend/components/preview/Phase*.tsx | wc -l  # 期望 12
```

---

## 端到端验证 (Phase 1-7 全部完成后)

```bash
# 1. 全量测试
.venv/bin/python3 -m pytest tests/ -x --timeout=30
cd src/frontend && npx vitest run

# 2. 路由对齐
.venv/bin/python3 -c "
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
assert len(double) == 0, f'DOUBLE: {double}'
print('ROUTES: OK')
"

# 3. 前端 /api/v1/ 残留
grep -rn '/api/v1/' src/frontend/ && echo "FAIL" || echo "PASS (no /api/v1/ residual)"

# 4. EVID_ 检查
grep -rn 'EVID_' src/backend/api/ | wc -l  # >0

# 5. proxy 检查
grep -rn 'proxy' src/frontend/vite.config.ts | wc -l  # >0

# 6. docker compose up 端到端 (手动)
# docker compose up -d
# curl http://localhost:8000/health
# docker compose down
```

---

## 风险与缓解

| 风险 | 等级 | 缓解 |
|------|------|------|
| Phase 2 路由修复涉及 7 文件 + main.py，遗漏导致回归 | 🔴 高 | GAPFIX-013 集成测试自动检测 missing/extra/double-prefix |
| Phase 4 event_bus 回调注入可能引入循环依赖 | 🟡 中 | 采用回调注入模式，在 main.py 启动时注册 broadcast handler |
| Phase 6 Whisper API token 权限不足 (已知问题) | 🟡 中 | 先实现接口抽象 + stub 回退，token 就绪后切换 |
| 全量测试回归 (2017+ tests) | 🟡 中 | 每 Phase 完成后跑全量 pytest，不等到最后 |
| TDD 循环中的测试可能写得太弱 (stub 可通过) | 🟡 中 | 按 HARNESS §4.2 Rule 5 自检: "Would a stub pass this test?" |

---

## 执行建议

1. **按 Phase 顺序执行**，Phase 1 是所有上层代码的地基，必须先完成
2. **每完成一个 Phase，运行其验证门禁 + 全量 pytest**，确保无回归
3. **每张 task card 独立 commit**，格式 `[SPEC-GAPFIX-NNN] <描述>`
4. **所有验证命令使用 `.venv/bin/python3 -m pytest`**，不使用裸 `pytest`
5. **Phase 2 是最危险的变更**，涉及 7 个文件 + main.py，需仔细验证 route diff
6. **预计总工作量**: ~31 张 task card × 5min = ~2.5 小时连续实施时间
