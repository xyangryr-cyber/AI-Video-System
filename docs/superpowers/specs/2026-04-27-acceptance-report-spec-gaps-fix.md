# SPEC 错漏修复 — 验收报告

> Date: 2026-04-27
> Inspector: AI Quality Check
> Source Spec: `docs/superpowers/specs/2026-04-26-spec-gaps-fix-design.md`
> Project: AI-Video-System @ `/Users/xyangryr/Desktop/硅基员工/AI-Video-System/`

---

## 总体结论: 🔴 未通过

**7 个成功标准中 0 个完全满足，7 个 Phase 中 0 个完成。** 该 SPEC 修复方案尚未被实施。当前代码库仍处于修复前的原状。

---

## 成功标准逐项验证

| # | 成功标准 | 状态 | 证据 |
|---|----------|------|------|
| 1 | `pytest tests/` 全部通过 | 🔴 BLOCKED | Python 3.9 与 deepeval 依赖不兼容（`X \| None` 语法需 3.10+），pytest 无法启动 |
| 2 | `vitest run` 全部通过 | 🟢 PASS | 259 tests passed, 48 files, 0 failures |
| 3 | Route diff: missing=0, extra=0, double-prefix=0 | 🔴 FAIL | missing=**17**, extra=**14**, double-prefix=**9** |
| 4 | `grep -rn '/api/v1/' src/frontend/` 返回空 | 🔴 FAIL | **13** 处残留（6 个源文件中） |
| 5 | `grep -rn 'EVID_' src/backend/api/` 返回 >0 | 🔴 FAIL | **0** 条 |
| 6 | `grep -rn 'proxy' src/frontend/vite.config.ts` 返回配置 | 🔴 FAIL | **无 proxy** |
| 7 | docker compose up 端到端验证 | 🔴 UNVERIFIABLE | 前置条件未满足（Phase 1-4 未完成） |

### Route Diff 详细数据

**missing (17 条)** — SPEC-1A 声明但未实现的路由:
```
DELETE /api/projects/{}
GET   /api/projects
GET   /api/projects/{}
GET   /api/projects/{}/costs
GET   /api/projects/{}/events
GET   /api/projects/{}/phases/{}/artifact
GET   /api/projects/{}/preferences
GET   /api/projects/{}/state
GET   /api/projects/{}/tasks
GET   /api/system/status
POST  /api/projects
POST  /api/projects/{}/advance
POST  /api/projects/{}/chat
POST  /api/projects/{}/preferences/confirm
POST  /api/projects/{}/rollback
POST  /api/projects/{}/skip
POST  /api/projects/{}/tasks/{}/cancel
```

**double-prefix (9 条)** — 双层 `/api/` 前缀:
```
/api/cost/api/projects/{}/cost
/api/observability/api/observability/status
/api/observability/api/projects/{}/artifacts
/api/observability/api/projects/{}/audit
/api/observability/api/projects/{}/events
/api/projects/api/projects/{}/preferences
/api/system/api/projects
/api/system/api/system/status
/api/tasks/api/projects/{}/tasks
```

根因: `main.py` 在 `app.include_router()` 中传了 `prefix=`，同时各 router 装饰器内又写了 `/api/...` 绝对路径，导致双叠。

### /api/v1/ 残留文件清单

| 文件 | 行号 |
|------|------|
| `mocks/handlers.ts` | 11, 12, 13, 17, 18 |
| `types/project.ts` | 1 |
| `components/CandidateSelector.tsx` | 22 |
| `hooks/useProjects.ts` | 12 |
| `hooks/useCreateProject.ts` | 10 |
| `hooks/usePreferenceWriteback.ts` | 29, 45 |
| `hooks/useEventStream.ts` | 12 |
| `hooks/useProjectState.ts` | 8 |

---

## Phase 逐项状态

### Phase 1: 合约层 (Layer 0) — 🔴 0/4

| 产出物 | 状态 |
|--------|------|
| `src/shared/contracts/event_types.py` | ❌ 不存在 |
| `src/shared/contracts/event_types.ts` | ❌ 不存在 |
| `src/shared/contracts/error_codes.py` | ❌ 不存在 |
| `src/shared/contracts/error_codes.ts` | ❌ 不存在 |
| `src/shared/contracts/api_routes.py` | ✅ 已存在（修复前即有） |
| `src/shared/contracts/api_routes.ts` | ✅ 已存在（修复前即有） |

### Phase 2: 路由层 — 🔴 1/9

| 检查项 | 当前状态 | 问题 |
|--------|----------|------|
| `system.py` 使用 `prefix="/api/system"` + 相对路径 | ❌ | 无 prefix，装饰器内写绝对路径 `/api/system/status` |
| `system.py` 移除 `POST /api/projects` | ❌ | 仍包含 |
| `observability.py` 使用 `prefix="/api"` + 相对路径 | ❌ | 无 prefix，装饰器内写绝对路径 `/api/observability/...`、`/api/projects/...` |
| `cost.py` 使用 `prefix="/api"` + 相对路径 | ❌ | 无 prefix，装饰器内写绝对路径。且 path 是 `cost` 单数（SPEC 为 `costs`） |
| `tasks.py` 使用 `prefix="/api"` + 相对路径 | ❌ | 无 prefix，装饰器内写绝对路径 |
| `preferences.py` 使用 `prefix="/api"` + 相对路径 | ❌ | 无 prefix，装饰器内写绝对路径 |
| `projects.py` 新建 | ❌ | 文件不存在 |
| `main.py` router 注册无额外 prefix + JSON 日志 | ❌ | 所有 include_router 都传了 prefix=，且无 JsonLineFormatter |
| `api/middleware/error_handler.py` | ❌ | 文件不存在 |

### Phase 3: 前端层 — 🔴 1/4

| 检查项 | 状态 | 证据 |
|--------|------|------|
| 删除 `/api/v1/` 前缀 | ❌ | 13 处残留 |
| `vite.config.ts` 添加 proxy | ❌ | `server: { port: 3000, host: "0.0.0.0" }` 无 proxy 块 |
| `types/events.ts` 同步 EventType 枚举 | ⚠️ | 文件存在，但仅定义了 `AgentEvent` 接口，未从共享合约导入（合约不存在） |
| apiClient 重构 | ❌ | 所有 hooks 直写 `/api/v1/...` 字面量 |

### Phase 4: WebSocket 事件广播 — 🔴 0/2

| 检查项 | 状态 | 证据 |
|--------|------|------|
| ConnectionManager (连接池 + broadcast) | ❌ | websocket.py 仅 50 行，只有 accept + ping/pong |
| event_bus 回调注入 | ❌ | `event_bus.py` 不存在 |
| WS broadcast 集成测试 | ❌ | 无对应测试文件 |

### Phase 5: 集成层 — 🔴 0/6

| 检查项 | 状态 | 证据 |
|--------|------|------|
| Pre-flight 真实检查器 | ❌ | 9 个检查器全部 `_stub_ok()` |
| hard claims 验证阻断 (gate_p8/p10/p11) | ❌ | 无 `check_hard_claims` |
| gate_registry 显式绑定 | ⚠️ | registry 机制存在，但 `gates/__init__.py` 不存在（无显式注册调用） |
| TaskType docstring "8 → 17" | ❌ | 仍写 "8 canonical task types" |
| agent_call_log + redact hook | ❌ | llm_service.py 无相关代码 |
| SQLite 备份脚本 | ❌ | `scripts/backup_sqlite.py` 不存在 |

### Phase 6: 媒体渲染 — 🔴 0/3

| 检查项 | 状态 | 证据 |
|--------|------|------|
| brand_kit_overlay 真实 Remotion | ❌ | Stub: 返回 `video_path.replace(".mp4", "_branded.mp4")` |
| Whisper 强制对齐 | ❌ | Stub: 均分字词时间，无 Whisper API 调用 |
| voice_direction PACE_MAP 对齐 | ❌ | 仍为 `{slow: 0.8, medium: 1.0, fast: 1.2}`，非 spec 要求的 5 级映射 |

### Phase 7: 长期一致性 — 🔴 0/5

| 检查项 | 状态 |
|--------|------|
| routes SDK 生成脚本 (`.py` + `.ts`) | ❌ 均不存在 |
| 枚举同步脚本 (`generate_event_types.py`, `generate_error_codes.py`) | ❌ 均不存在 |
| `check_spec_coverage.py` | ❌ 不存在 |
| 12 个 Phase preview 组件 | ⚠️ 仅 P4/P5/P6/P7A 存在（4/12） |
| `utils/errorUxMap.ts` + `ErrorState.tsx` | ✅ 均存在 |
| `Remotion/PreviewComposition.tsx` 真实接入 | ❌ 文件不存在 |

---

## 测试覆盖现状

### vitest (前端)
```
Test Files  48 passed (48)
     Tests  259 passed (259)
```
前端测试基础设施运行正常。

### pytest (后端)
```
🔴 BLOCKED — Python 3.9 + deepeval 类型注解不兼容
  TypeError: unsupported operand type(s) for |: '_GenericAlias' and 'NoneType'
```
需升级 Python ≥ 3.10，或降级 deepeval。

### 缺失的关键测试
- Phase 1: event_types / error_codes 合约测试 — 不存在
- Phase 2: 路由双重前缀检测测试 — 不存在
- Phase 4: WebSocket broadcast 集成测试 — 不存在
- Phase 5: preflight 真实检查器测试 — 不存在
- Phase 6: Whisper / brand_kit 测试 — 均为 stub 级别

---

## 统计汇总

| 维度 | 完成/总数 | 完成率 |
|------|-----------|--------|
| Phase 1 (合约层) | 0/4 | 0% |
| Phase 2 (路由层) | 0/9 | 0% |
| Phase 3 (前端层) | 0/4 | 0% |
| Phase 4 (WebSocket) | 0/2 | 0% |
| Phase 5 (集成层) | 0/6 | 0% |
| Phase 6 (媒体渲染) | 0/3 | 0% |
| Phase 7 (长期一致性) | 0/5 | 0% |
| **总体** | **0/33 项** | **0%** |

---

## 风险与建议

1. **Python 版本问题**: pytest 无法运行，需先修复环境（升级 Python 或降级 deepeval）才能执行 TDD 循环。
2. **实施顺序**: 必须从 Phase 1 开始，合约层是所有上层代码的基础。event_types 和 error_codes 缺失导致 Phase 2/4/7 均被阻塞。
3. **路由修复是最危险的变更**: 涉及 6 个 route 文件 + main.py + 前端 8 个文件，需精确执行避免遗漏。
4. **预估工作量**: ~31 张 task card，每张 2-5 分钟粒度 → 约 2-4 小时连续实施时间。
