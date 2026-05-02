# SPEC-P0-FIX-002: ChatInput 接入真实 Chat API

> **来源 Bug**: BUG-002 (handleSend 空函数)
> **根因**: WorkflowPage.tsx:43-45 的 `handleSend` 是空函数体，注释写 "mock 模式不真实发送"
> **严重级别**: CRITICAL — 阻塞场景 2（对话修改需求）全部子场景
> **依赖**: SPEC-P0-FIX-001（需要先有真实数据层）

---

## 根因分析

```typescript
// WorkflowPage.tsx:43-45 — 当前状态
const handleSend = () => {
  // mock 模式不真实发送，留待后续接入 API
}
```

ChatInput 组件本身功能完整（`ChatInput.tsx` 管理本地 state、支持 Enter 发送），但父组件传入的 `onSend` 回调是空函数。后端 `POST /api/projects/:id/chat` 已实现，接受 `{ message: string, context?: {} }` 并返回 Agent 响应。

**缺失的部分**: 没有自定义 hook 用于发送 chat 消息和管理消息列表。需要新建 `useChat` hook 或扩展 `useProjectState`。

---

## Acceptance Criteria

| # | AC | 验证方式 |
|---|-----|---------|
| AC-1 | 用户在 ChatInput 输入文本并点击发送后，消息出现在对话区 | Playwright: 输入"把时长改成15分钟"，发送后对话区出现该消息 |
| AC-2 | 发送后立即在对话区显示用户消息（乐观更新），不等待 API 响应 | Playwright: 点击发送后 < 500ms 消息出现在对话区 |
| AC-3 | 发送后 POST `/api/projects/:id/chat` 被调用，参数 `{ message: 用户输入 }` | Playwright: 验证网络请求 |
| AC-4 | Agent 回复渲染在对话区（在用户消息下方） | Playwright: 等待 Agent 回复出现并验证内容非空 |
| AC-5 | 加载中状态：Agent 思考时对话区底部显示 "正在分析..." | Playwright: 验证加载指示器 |
| AC-6 | 发送后输入框清空，发送按钮恢复可用 | Playwright: 验证输入框为空 + 按钮可用 |
| AC-7 | 空消息/纯空白消息不发送（ChatInput 已有此逻辑，确保不被破坏） | Playwright: 输入空白后按钮 disabled |
| AC-8 | API 失败时在对话区显示错误消息，用户可重试 | Playwright: 模拟网络错误验证 |

---

## TDD 实现计划

### RED 1: useChat hook 测试

```typescript
// tests/unit/frontend/hooks/useChat.test.ts
// 测试 useChat hook:
// 1. sendMessage 调用 apiClient.post('/api/projects/:id/chat', { message })
// 2. sendMessage 后 messages 列表包含用户消息（乐观更新）
// 3. API 返回后 messages 列表包含 agent 回复
// 4. isLoading 在请求期间为 true
// 5. API 失败时 error 状态正确设置
```

### RED 2: WorkflowPage 集成测试

```typescript
// tests/unit/frontend/WorkflowPage.test.tsx
// mock useChat hook:
// 1. 断言 ChatInput onSend 连接到了 useChat.sendMessage
// 2. 断言 ChatHistory messages 来自 useChat.messages
// 3. 断言发送中状态正确传递给 ChatInput
```

### GREEN 1: 创建 useChat hook

```typescript
// src/frontend/hooks/useChat.ts
export function useChat(projectId: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = async (text: string) => {
    // 1. 乐观更新: 添加用户消息到 messages
    // 2. POST /api/projects/:id/chat
    // 3. 添加 agent 回复到 messages
    // 4. 错误处理
  };

  return { messages, sendMessage, isLoading, error };
}
```

### GREEN 2: 接入 WorkflowPage

```typescript
// WorkflowPage.tsx
// 1. import useChat
// 2. const { messages, sendMessage, isLoading } = useChat(id)
// 3. ChatHistory messages={messages}
// 4. ChatInput onSend={sendMessage} disabled={isLoading}
// 5. 发送中显示 loading 指示器
```

### GREEN 3: 错误处理

```typescript
// useChat.ts
// catch 块: setError(error.message)
// WorkflowPage.tsx
// error && <ErrorMessage message={error} onDismiss={clearError} />
```

### REFACTOR

- 提取 chat message 类型到共享类型
- 考虑从 `useProjectState` 获取历史消息（events 表）初始化 useChat
- 优化 agent 消息的卡片渲染（复用 P0RequirementsView 的数据展示）

---

## 允许修改的文件

| 文件 | 用途 |
|------|------|
| `src/frontend/hooks/useChat.ts` | **新建** — Chat hook |
| `src/frontend/pages/WorkflowPage.tsx` | 接入 useChat |
| `src/frontend/components/workflow/ChatHistory.tsx` | 可能需要支持 loading/error 状态 |
| `tests/unit/frontend/hooks/useChat.test.ts` | 新增 |
| `tests/unit/frontend/WorkflowPage.test.tsx` | 更新 |

## 禁止修改的文件

- `src/frontend/components/workflow/ChatInput.tsx`（功能完整，不需要改）
- `src/frontend/components/workflow/mockData.ts`
- `src/backend/api/routes/projects.py`（Chat API 已实现）

---

## 验证命令

```bash
# Hook 单元测试
cd src/frontend && npx vitest run tests/unit/frontend/hooks/useChat.test.ts

# 集成测试
cd src/frontend && npx vitest run tests/unit/frontend/WorkflowPage.test.tsx

# E2E 验证 (Playwright)
# 1. 创建项目 → 进入 WorkflowPage
# 2. 在 ChatInput 输入"把时长改成15分钟"
# 3. 点击发送 → 消息出现在对话区
# 4. 等待 Agent 回复出现
# 5. 输入空白 → 发送按钮 disabled
```
