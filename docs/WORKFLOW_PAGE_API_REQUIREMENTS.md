# WorkflowPage 后端接口需求

> 关联代码：`src/frontend/pages/WorkflowPage.tsx` + `src/frontend/components/workflow/*`
> 关联提交：`a43048ee [SPEC-E-UI-V2] redesign WorkflowPage with new collaborative terminal layout`
> 当前状态：前端用 mock 数据；本文档定义将 mock 切换为真实数据所需的后端接口。
> 写作日期：2026-04-30

---

## 1. 背景

新版 WorkflowPage 采用两栏布局：
- **左主栏**（中间视觉重心）：顶部 Header（项目名+阶段进度）→ 滚动对话区 → 底部任务卡 + 输入框
- **右侧栏**：上半部「阶段产物倒序列表」+ 下半部「关键事实核实」
- **弹窗层**：点击阶段产物卡片打开，内嵌 `PhasePreviewRouter` 展示该阶段产物详情

为支撑该 UI 全功能联调，需要 8 个数据源（5 个已有端点可复用、2 个新端点、1 个 WebSocket 订阅）。

---

## 2. UI 元素 → API 映射总表

| # | UI 区域 | 数据需求 | 来源 | 状态 |
|---|---|---|---|---|
| 1 | Header 标题 + ID | `project.title` / `project.id` | `GET /api/projects/{id}` | ✅ 已有 |
| 2 | Header 阶段进度（"阶段 12/12 · 精剪交付"） | `current_phase` + 总阶段数 | `GET /api/projects/{id}/state` | ✅ 已有 |
| 3 | 对话流（Agent + 用户气泡） | 历史聊天消息列表 | `GET /api/projects/{id}/chat/history` ⚠️ | 🆕 **新增** |
| 4 | 对话流实时新消息 | 增量消息推送 | WebSocket `chat.message` | 🆕 **新事件** |
| 5 | 任务卡片（标题 + N/N + 子任务列表） | 当前阶段任务账本 | `GET /api/projects/{id}/tasks?phase={current_phase}` | ✅ 已有，需加 query 参数 |
| 6 | 输入框发送 | 提交用户消息 | `POST /api/projects/{id}/chat` | ✅ 已有 |
| 7 | 阶段产物列表（右上栏，倒序） | `phases[]`（带状态、artifact_url） | `GET /api/projects/{id}/state` 复用 | ✅ 已有 |
| 8 | 关键事实核实（右下栏） | Claims 列表 | `GET /api/projects/{id}/claims` ⚠️ | 🆕 **新增** |
| 9 | 阶段产物弹窗内容 | 单阶段 artifact JSON | `GET /api/projects/{id}/phases/{phase}/artifact` | ✅ 已有 |
| 10 | 全局实时同步（阶段推进、任务完成） | 状态变更事件 | WebSocket `phase.advanced`, `task.updated`, `artifact.produced` | ✅ 已有（SPEC-11A） |

---

## 3. 已有端点（直接复用，无需后端改动）

### 3.1 `GET /api/projects/{id}` — 项目基础信息
**用途**：Header 渲染项目标题 + ID
**响应（关心字段）**：
```ts
{
  id: string,
  title: string,
  description: string,
  // ...
}
```

### 3.2 `GET /api/projects/{id}/state` — 项目完整状态
**用途**：
- Header 阶段进度（`current_phase` + 总数）
- 右上栏阶段产物列表（`phases[]` 派生）

**响应（关心字段，参考 SPEC-0A.3）**：
```ts
{
  project: { id, title, current_phase, status },
  phases: Array<{
    phase_num: number,        // 0..12
    status: 'pending' | 'running' | 'completed' | 'failed',
    artifact_version: number,
    artifact_status: 'ok' | 'damaged' | 'missing' | null,
    artifact_url: string | null,  // /api/projects/{id}/phases/{n}/artifact
    started_at: string | null,
    completed_at: string | null,
  }>,
  // ...
}
```

**前端派生逻辑**：
- 列表 = `phases.filter(p => p.phase_num <= current_phase).reverse()`
- "In Progress" 标签 = `phases[i].phase_num === current_phase`

### 3.3 `POST /api/projects/{id}/chat` — 发送消息
**用途**：底部输入框点发送
**请求**：
```ts
{ message: string }
```
**响应**：
```ts
{ action: string, response: string, ... }  // 由 IntentRouter 决定
```
**前端期望**：发送成功后 WebSocket 推送 `chat.message` 事件，前端追加到对话流（不依赖 HTTP 响应做 UI 更新，避免双写）。

### 3.4 `GET /api/projects/{id}/phases/{phase}/artifact` — 单阶段产物
**用途**：弹窗内 `PhasePreviewRouter` 数据源（前端 `useArtifact` hook 已封装）
**响应**：
```ts
{ artifact_data: Record<string, unknown> | null }
```

### 3.5 WebSocket `/ws/projects/{id}` — 实时事件流
**用途**：实时刷新页面状态
**前端订阅事件类型**（SPEC-11A）：
- `phase.advanced` → 重新拉 `/state`，更新阶段产物列表与 In Progress 标签
- `task.updated` → 重新拉 `/tasks`，更新任务卡片进度与子项状态
- `artifact.produced` → 重新拉 `/state`，新阶段产物卡片可点击
- `chat.message` 🆕 → 追加到对话流（**新事件类型，需后端在 chat 路由中触发广播**）

---

## 4. 已有端点 + 微调

### 4.1 `GET /api/projects/{id}/tasks` — 任务账本
**改动**：增加可选 query 参数 `phase`，过滤当前阶段任务。

**当前**：
```
GET /api/projects/{id}/tasks
→ { tasks: Task[] }   // 全部阶段
```

**期望**：
```
GET /api/projects/{id}/tasks?phase={n}&include_subtasks=true
→ {
  tasks: [
    {
      task_id: string,
      title: string,                  // 主任务标题（任务卡顶部展示）
      phase: number,
      status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled',
      subtasks: [                     // 任务卡展开后的子任务列表
        {
          subtask_id: string,
          title: string,              // 子任务文案
          status: 'pending' | 'completed',
          order: number,              // 1..N，决定展示顺序
        }
      ],
      progress: { completed: number, total: number }, // 任务卡右侧 "5/5"
    }
  ]
}
```

**前端期望行为**：返回**当前阶段最多 1 条 active 任务**（任务卡只展示一个主任务）。如果当前阶段无 active 任务返回空数组，前端展示"等待中"占位。

---

## 5. 新增端点

### 5.1 🆕 `GET /api/projects/{id}/chat/history` — 对话历史

**为什么不直接用 `GET /events`？**
`/events` 用于 Agent 活动面板（系统级事件流），事件粒度与 chat 不一致：events 包含产物生成、Gate 检查、Agent 调用等系统消息；而 chat history 只关心用户与 Agent 的对话气泡。混用会导致前端要做大量过滤逻辑且语义不清。

**端点设计**：
```
GET /api/projects/{id}/chat/history?limit=50&before={message_id}
→ {
  messages: [
    {
      message_id: string,           // 单调递增或 ULID
      role: 'agent' | 'user' | 'system',
      content: string,              // 消息正文（Markdown allowed）
      agent_name?: string,          // role=agent 时填，例 "VideoEngine Agent"
      phase: number | null,         // 消息发出时的当前阶段（用于跨阶段历史回溯）
      created_at: string,           // ISO 8601
      metadata?: {
        intent?: string,            // IntentRouter 分类结果
        cost_usd?: number,
        tokens?: { input: number, output: number },
      },
    }
  ],
  has_more: boolean,
  next_cursor: string | null,
}
```

**关键约束**：
1. 默认按 `created_at` **升序**返回（历史消息按时间从早到晚），分页用 `before` 游标向更早翻
2. 只返回 `chat.message` 类型记录，**不**返回系统事件
3. 持久化层建议：新建表 `chat_messages`，schema 见 §6.1

### 5.2 🆕 `GET /api/projects/{id}/claims` — 关键事实核实清单

**为什么需要新端点？**
SPEC-A 已定义 Claim 数据模型（SPEC-0A.8 + `frontend/types/claim.ts`），但**没有暴露查询接口**。WorkflowPage 右下栏需要全局事实清单，无法从现有 `/state` 派生。

**端点设计**：
```
GET /api/projects/{id}/claims?status=verified&type=fact&limit=50
→ {
  claims: [
    {
      claim_id: string,                    // 例 "claim_2_001" → UI 显示为 "F1"
      display_id: string,                  // 例 "F1" / "F2"（按 verified 顺序生成）
      content: string,                     // 例 "2025年第一季度全球央行净购金量为290吨"
      claim_type: 'fact' | 'data' | 'event' | 'citation' | 'image_backed',
      verification_status: 'verified' | 'unverified' | 'user_disputed' | 'superseded',
      source: {
        name: string,                      // "世界黄金协会 (WGC)"
        url: string,                       // 外链
        method: string,                    // "官方报告交叉验证"
      },
      usage: string[],                     // 引用位置 ["S2E1", "P4", "P6"]
      source_phase: number,                // 首次产生于哪个阶段
      verified_at: string | null,
    }
  ],
  total: number,
}
```

**关键约束**：
1. 默认仅返回 `verification_status='verified'` 的 claim（右下栏标题就叫"关键事实核实"）
2. `display_id` 由后端按 verified 顺序生成，前端直接展示，不做计算
3. `usage` 字段用于「这条事实被哪些段落引用」，可空数组

**Query 参数**：
| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `status` | enum | `verified` | 过滤验证状态；传 `all` 返回全部 |
| `type` | enum | （不限） | 过滤 claim 类型 |
| `phase` | int | （不限） | 仅返回 source_phase 匹配的 claim |
| `limit` | int | 50 | 最多返回数 |

---

## 6. 数据库 Schema 建议

### 6.1 `chat_messages` 表（新建）
```sql
CREATE TABLE chat_messages (
  message_id    TEXT PRIMARY KEY,           -- ULID
  project_id    TEXT NOT NULL,
  role          TEXT NOT NULL CHECK(role IN ('agent','user','system')),
  agent_name    TEXT,                       -- role=agent 时填
  content       TEXT NOT NULL,
  phase         INTEGER,                    -- 发出时的当前阶段
  intent        TEXT,                       -- IntentRouter 输出
  cost_usd      REAL,
  tokens_input  INTEGER,
  tokens_output INTEGER,
  created_at    TEXT NOT NULL,              -- ISO 8601
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
CREATE INDEX idx_chat_messages_project_time ON chat_messages(project_id, created_at);
```

**写入触点**：
- 用户调用 `POST /api/projects/{id}/chat` → 写一条 `role='user'` 记录
- IntentRouter / Agent 产生回复 → 写一条 `role='agent'` 记录
- 系统级提示（如阶段切换通知）→ `role='system'` 记录（可选）

### 6.2 `claims` 表
SPEC-0A.8 已定义 Claim 数据模型；按现有 schema 实现，本文档不重复。`GET /claims` 端点直接对该表查询。

如果当前 `claims` 表已存在但缺 `display_id` 字段：
```sql
ALTER TABLE claims ADD COLUMN display_id TEXT;
-- 迁移脚本：按 verified_at ASC 顺序填充 F1, F2, F3...
```

---

## 7. WebSocket 事件订阅（需要补充的事件类型）

WorkflowPage 已通过 `useWebSocket(projectId)` 订阅 `/ws/projects/{id}`。需要补充：

| 事件名 | Payload | 触发时机 | 状态 |
|---|---|---|---|
| `chat.message` 🆕 | `{ message_id, role, content, agent_name?, phase, created_at }` | 写入 `chat_messages` 表后立即广播 | 🆕 后端需补 |
| `claim.added` 🆕 | `{ claim_id, display_id, content, source }` | 新 claim verified 后 | 🆕 后端需补 |
| `claim.updated` 🆕 | `{ claim_id, verification_status }` | claim 状态变化 | 🆕 后端需补 |
| `phase.advanced` | `{ from_phase, to_phase }` | 阶段推进 | ✅ 已有（SPEC-11A） |
| `task.updated` | `{ task_id, phase, status, progress }` | 任务状态变化 | ✅ 已有（SPEC-11A） |
| `artifact.produced` | `{ phase_num, version, artifact_path }` | 产物生成 | ✅ 已有（SPEC-11A） |

---

## 8. 前端迁移计划（mock → 真实数据）

按依赖顺序，分 5 步替换 `src/frontend/components/workflow/mockData.ts` 中的 mock 数据：

| 步骤 | 替换内容 | 依赖端点 | 风险 |
|---|---|---|---|
| Step 1 | Header 项目标题/ID/阶段 | `GET /projects/{id}` + `/state` | 低（端点已有） |
| Step 2 | 阶段产物列表（右上栏） | `GET /projects/{id}/state` 派生 | 低（端点已有） |
| Step 3 | 任务卡（底部） | `GET /projects/{id}/tasks?phase={n}` | 中（需后端加 phase 参数 + subtasks） |
| Step 4 | 对话流（中栏） | `GET /chat/history` + WS `chat.message` | 高（需新建表 + 端点 + WS 事件） |
| Step 5 | 关键事实核实（右下栏） | `GET /claims` + WS `claim.added/updated` | 高（需新端点 + WS 事件） |

每步独立 PR，前端用 `feature flag` 控制（或临时保留 mock 兜底），逐步切换。

---

## 9. 验收清单（后端实施完成的判定）

- [ ] `GET /api/projects/{id}/chat/history` 返回 chat_messages 表数据，分页正确
- [ ] `GET /api/projects/{id}/claims` 默认只返回 verified claims，display_id 升序稳定
- [ ] `GET /api/projects/{id}/tasks` 接受 `?phase=N` 参数并返回 subtasks 字段
- [ ] WebSocket 在 `POST /chat` 后真实广播 `chat.message` 事件，新前端能收到并追加气泡
- [ ] 前端把 `mockData.ts` 全部替换为 hook 调用后，UI 行为与现有 mock 模式一致（视觉 + 交互不退化）
- [ ] SPEC-A-contracts.md 同步更新：API 路由总表追加 `/chat/history` 与 `/claims` 两行；SPEC-11A 追加 `chat.*` / `claim.*` 事件类型

---

## 10. 待决策点（需要业务方确认）

1. **Chat 历史保留时长**：是否永久保留？还是只保留最近 N 条 / N 天？（影响表索引与归档策略）
2. **Claims 与 Project 的归属**：所有 claim 是否都强绑定到一个 project_id？跨项目复用 claim 是否需要？（影响表设计是否要 `project_id` 外键）
3. **System 类消息**（"阶段已推进至 P5" 这类）是否进 chat 流？还是只走 events 面板？（截图里没体现）
4. **离线场景**：用户重新打开页面时是否要把 chat 全量历史一次性下发，还是分页？默认 limit=50 + 向上滚动加载更多？

业务方答复后，本文档进入 SPEC-A 修订流程，落入 `docs/specs/SPEC-A-contracts.md` 正式契约。
