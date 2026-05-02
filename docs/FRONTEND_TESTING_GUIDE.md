# AI-Video-System 前端真实用户测试方法

> 写给 AI Agent 的操作手册。无需探索，直接执行。

---

## 架构速览

```
浏览器 (localhost:3000)
  → src/frontend/ (Vite + React, 真前端)
  → ? MSW 拦截 (默认开启，返回假数据)
  → 后端 FastAPI (需要单独启动)
  → SQLite 数据库
```

**重要**: 还有一个 `prototype/` 目录，是纯 UI 原型（所有数据写死在代码里），不是真实前端。测试一律用 `src/frontend/`。

---

## MSW 说明（必读）

MSW = Mock Service Worker = 浏览器里的"假服务员"。

**默认行为**: 执行 `npm run dev` 启动前端时，MSW 自动启动，拦截 API 请求并返回本地 JSON 文件里的假数据。后端完全不被访问。

**关键代码**: `src/frontend/main.tsx` 第 7 行:
```ts
if (import.meta.env.DEV && !import.meta.env.VITE_DISABLE_MSW) {
  // MSW 启动，拦截一切
}
```

## 两种测试模式

### 模式 A: 连真实后端（推荐用于功能测试）

**前提**: 后端必须先启动。

```bash
# 终端 1: 启动后端
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System
source .venv/bin/activate
uvicorn src.backend.api.main:app --reload --port 8000

# 终端 2: 启动前端（禁用 MSW）
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System/src/frontend
VITE_DISABLE_MSW=1 npm run dev
# 前端在 http://localhost:3000
```

**预期行为**:
- 项目列表从数据库查询（新建数据库时为空列表，显示"暂无项目"）
- 新建项目写入真实数据库
- Chat 请求调用 IntentRouter（关键词匹配）

### 模式 B: 用 MSW 假数据（仅适合看 UI 样式）

```bash
cd /Users/xyangryr/Desktop/硅基员工/AI-Video-System/src/frontend
npm run dev
# MSW 默认开启，所有数据来自 tests/fixtures/api/projects/*.json
```

**MSW 拦截清单** (`src/frontend/mocks/handlers.ts`):

| API 请求 | 返回的 JSON 文件 | 注意 |
|---|---|---|
| `GET /api/projects` | `list_response.json` | 永远返回 3 个项目 |
| `GET /api/projects/:id/state` | `state_proj_001.json` | **有 Bug: 忽略 :id，永远返回 proj_001 数据** |
| `POST /api/projects` | `create_response.json` | 永远返回 `proj_new_001` |
| `GET /api/projects/:id/events` | `events/list_response.json` | - |
| `POST /api/projects/:id/chat` | **没有 handler** | 请求穿透到后端，后端没启动就报错 |
| `POST /api/projects/:id/advance` | **没有 handler** | 同上 |

---

## 关键 Fixture 文件内容

### `list_response.json` (项目列表)
```
proj_001: "黄金价格走势分析" (行业分析, phase 2, 进度 25%)
proj_002: "十五五规划解读" (政策解读, phase 1, 进度 10%)
proj_003: "AI 行业周报" (行业分析, phase 8, 进度 70%)
```

### `state_proj_001.json` (项目详情)
```
project_id: proj_001
title: "波动率大师"
current_phase: 3
phases: P0-P2 completed, P3 active
```

### `create_response.json` (新建项目响应)
```
id: "proj_new_001"
title: "New Project" (注意: 不是用户输入的标题)
```

---

## 页面路由对照

| URL | 页面组件 | 功能 |
|---|---|---|
| `/projects` | `pages/ProjectList.tsx` | 项目列表 |
| `/projects/new` | `pages/NewProject.tsx` + `components/CreateProjectForm.tsx` | 新建项目表单 |
| `/projects/:id` | `pages/ProjectRedirect.tsx` | 自动重定向到 phase 0 |
| `/projects/:id/phases/:phase` | `pages/WorkflowPage.tsx` | 阶段工作流页（左侧阶段导航 + 中间对话 + 右侧产物预览） |
| `/settings` | `pages/SettingsPage.tsx` | 设置页 |

---

## 已知问题清单

1. **MSW `:id` Bug**: `handlers.ts:12` 的 `GET /api/projects/:id/state` handler 完全忽略了 `:id` 参数，总是返回 `state_proj_001.json`。访问任意 project ID 都看到"波动率大师"。

2. **P0 需求澄清 Agent 缺失**: 新建项目后进入 Phase 0，不会主动弹出 AI 澄清问题。后端 `POST /api/projects` 创建记录后不做任何 Agent 调用。`IntentRouter.classify()` 是关键词匹配器，不调用 LLM。

3. **Chat 请求无 MSW handler**: `POST /api/projects/:id/chat` 没有 MSW mock，在只有前端运行时会静默失败。

4. **创建响应未返回用户输入**: `create_response.json` 的 title 字段是硬编码的 "New Project"，不是用户在表单输入的实际标题。

---

## 快速验证命令

```bash
# 检查后端是否在运行
curl http://localhost:8000/health

# 检查真实项目数据
curl http://localhost:8000/api/projects

# 创建测试项目（真实后端）
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{"title": "测试项目", "description": "测试描述内容至少十个字"}'

# 查看项目状态
curl http://localhost:8000/api/projects/<project_id>/state

# 前端类型检查
cd src/frontend && npx tsc --noEmit

# 前端测试
cd src/frontend && npx vitest run
```
