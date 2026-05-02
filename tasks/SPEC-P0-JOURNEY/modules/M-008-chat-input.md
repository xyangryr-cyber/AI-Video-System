# SPEC-M-008: Chat Input + Interaction Area

## Metadata

```yaml
spec_id: SPEC-M-008
delivery_kind: module
parent_journey: SPEC-J-002
evidence_type: user_observable
status: PENDING
allowed_files:
  - "src/frontend/components/workflow/ChatInput.tsx"
  - "src/frontend/hooks/useChat.ts"
forbidden_files: ["HARNESS.md", "CLAUDE.md", ".claude/**"]
```

## Why This Module Exists

ChatInput 是用户在 Phase 0 对话区与系统交互的唯一入口。用户通过它发送 revise/regenerate/request_advance 等指令。输入框在 RequirementsAgent 运行期间仍然可用（用户可以提前输入下一条指令），Router 识别结果显示在对话区。关键设计：输入框永远可用，不因 Agent 运行中而 disabled——这样用户可以"提前排队"指令。

## Consumer / Evidence

### evidence_type: user_observable

| Field | Value |
|---|---|
| Closed by journey | SPEC-J-002（journey 的 playwright test 覆盖对话交互） |
| Note | 此模块不运行独立的 user-observable 测试 |

## Interfaces

| name | params | returns | raises | example |
|---|---|---|---|---|
| `ChatInput` | `projectId: string, onSend: (msg) => void` | React component | — | 对话区底部输入框 |
| `useChat` hook | `projectId: string` | `{messages, send, isLoading, error}` | — | 管理对话状态 + API 调用 |

## Data Constraints

| target | rules |
|---|---|
| 输入框 | 永远可用（不因 Agent 运行中而 disabled）；支持 Enter 发送 |
| 对话区消息 | 用户消息 + Agent 回复卡片按时间序排列；Agent 运行中显示 "正在分析你的需求..." |
| Router clarify | 前端渲染追问选项（如"修改需求"/"进入下一阶段"），用户点击后发送对应指令 |

## Exception Handling

| scenario | trigger | expected |
|---|---|---|
| 发送空消息 | message.trim() === "" | 不发送，输入框内容清空并恢复焦点 |
| API 调用超时 | revise/regenerate 超过 120s | 显示"请求超时，请重试"，用户可重新发送 |
| 网络断开 | fetch 失败 | 显示"消息发送失败，点击重试"，消息保留在输入框中 |

## Verification Commands

- `npx vitest run tests/unit/frontend/hooks/useChat.test.tsx`
- `npx vitest run tests/unit/frontend/workflow/ChatInput.test.tsx`
- `npx playwright test tests/e2e/playwright/phase0-J-002-iterate.spec.ts`

## Definition of Done

- [ ] 输入 revise 指令 → 消息发送 → Router 识别 → 卡片更新
- [ ] 输入 regenerate 指令 → 消息发送 → 卡片重建
- [ ] 输入模糊指令 → Router clarify → 追问选项渲染
- [ ] Agent 运行中 → 输入框仍可用（不 disabled）
- [ ] 空消息不发送
- [ ] Parent journey SPEC-J-002 playwright test 通过
