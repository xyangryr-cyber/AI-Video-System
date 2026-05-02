# Phase 0 手动测试 Bug 报告

> 测试日期: 2026-04-30
> 测试方法: Playwright 浏览器自动化，通过前端 UI 操作
> 测试环境: Backend (localhost:8000) + Frontend (localhost:3000, VITE_DISABLE_MSW=1)
> 测试文件: `tests/e2e/playwright/phase0-manual-scenarios.spec.ts`

---

## 总体测试结果

| 指标 | 数值 |
|------|------|
| 总检查点数 | 42 |
| PASS | 17 |
| FAIL | 17 |
| PARTIAL | 5 |
| SKIP | 3 |
| 通过率 | 40.5% |
| 含 PARTIAL 通过率 | 52.4% |

---

## 测试场景汇总

| 场景 | 测试项 | 结果 |
|------|--------|------|
| 1. 创建项目+生成需求定义 | 步骤 1.1 进入创建页 | ✅ PASS (3/3) |
| 1. 创建项目+生成需求定义 | 步骤 1.2 表单提交 | ❌ FAIL — 表单提交通道不稳定 |
| 1. 创建项目+生成需求定义 | 步骤 1.3 Agent 生成 | ❌ FAIL — WorkflowPage 使用 mock 数据 |
| 1. 创建项目+生成需求定义 | 步骤 1.4 审核+推进 | ❌ FAIL — 无 advance 按钮 |
| 2. 自然对话修改需求 | 步骤 2.1 revise 时长 | ❌ FAIL — ChatInput handleSend 是空函数 |
| 2. 自然对话修改需求 | 步骤 2.2 revise 平台 | ❌ FAIL — 同上 |
| 2. 自然对话修改需求 | 步骤 2.3 regenerate | ❌ FAIL — 同上 |
| 2. 自然对话修改需求 | 步骤 2.4 clarify | ❌ FAIL — 同上 |
| 3. 澄清问题处理 | 步骤 3.1 不完整描述 | ❌ FAIL — 无澄清区域 |
| 3. 澄清问题处理 | 步骤 3.2 补充信息 | ❌ FAIL — mock 数据不反映 |
| 3. 澄清问题处理 | 步骤 3.3 审核通过 | ❌ FAIL — mock 数据 |
| 4. 偏好提取与确认 | 全流程 | ❌ FAIL — 无完整交互 |
| 5. 门禁与推进 | 跨项目复用 | ❌ FAIL — 无实际 GateKeeper |
| 6. 输入校验 | 步骤 6.1 短描述 | ✅ PASS |
| 6. 输入校验 | 步骤 6.2 标题为空 | ✅ PASS |
| 6. 输入校验 | 步骤 6.3 页面恢复 | ❌ FAIL |
| 7. UI 交互细节 | 项目列表页 | ✅ PASS (3/3) |
| 7. UI 交互细节 | WorkflowPage UI | ❌ FAIL — mock 数据 |

---

## Bug 详细清单

### BUG-001 [CRITICAL] WorkflowPage 使用硬编码 Mock 数据，不连接后端

**文件**: `src/frontend/pages/WorkflowPage.tsx`
**行号**: 11-17
**严重级别**: CRITICAL — 阻塞所有 Phase 0 核心场景

**问题描述**:
WorkflowPage 完全使用从 `mockData.ts` 导入的硬编码数据，不调用任何后端 API：

```typescript
// WorkflowPage.tsx:11-17
import {
  MOCK_CURRENT_TASK_TITLE,
  MOCK_FACTUAL_DATA,
  MOCK_MESSAGES,
  MOCK_PROJECT_TITLE,
  MOCK_TASKS,
} from "@frontend/components/workflow/mockData"
```

**用户影响**:
- 进入任意项目的 Phase 0 页面，都看到相同的对话消息："我已经根据大纲生成了第 2 版结构化脚本..."
- 项目标题始终显示 "黄金价格走势分析与投资展望"（MOCK_PROJECT_TITLE）
- 无论项目实际处于哪个 Phase，任务清单始终显示 5 个固定 mock 任务
- RequirementsAgent 的真实输出完全不可见

**根因**: 提交 `a43048ee [SPEC-E-UI-V2]` 在重新设计 WorkflowPage 时引入了 mock 数据，但未接入后端 API。

**修复方向**: WorkflowPage 需要：
1. 使用 `useProjectState(id)` 获取真实项目数据
2. 使用 `useChat(id)` 获取真实对话历史
3. 使用 `useTasks(id)` 获取真实任务状态

---

### BUG-002 [CRITICAL] ChatInput 发送功能是空函数，对话完全不可用

**文件**: `src/frontend/pages/WorkflowPage.tsx`
**行号**: 43-45
**严重级别**: CRITICAL — 阻塞场景 2（对话修改需求）全部子场景

**问题描述**:
```typescript
// WorkflowPage.tsx:43-45
const handleSend = () => {
  // mock 模式不真实发送，留待后续接入 API
}
```

用户在聊天输入框输入文本并点击发送后：
1. 输入框内容被清空（ChatInput 组件本地状态更新）
2. 不调用任何后端 API（无 `/api/projects/:id/chat` POST 请求）
3. 消息不追加到对话区
4. 无 Agent 响应

**测试验证**: 输入 "把时长改成 15 分钟吧" 并点击发送，消息从输入框消失但对话区无变化。

---

### BUG-003 [HIGH] PhaseNavigation 组件未在 WorkflowPage 中渲染

**文件**: `src/frontend/pages/WorkflowPage.tsx`
**严重级别**: HIGH — 用户无法在 WorkflowPage 中切换阶段

**问题描述**:
`components/PhaseNavigation.tsx` 已实现完整的阶段导航组件（含 13 个阶段的按钮、完成/活跃状态指示、tooltip），但 WorkflowPage 未导入或使用该组件。

```
[data-testid="phase-nav-sidebar"] — 不存在于当前 WorkflowPage DOM 中
[data-testid="phase-nav-0"] — 不存在
```

---

### BUG-004 [HIGH] 项目标题始终显示 Mock 值

**文件**: `src/frontend/pages/WorkflowPage.tsx:62`
**严重级别**: HIGH

**问题描述**:
```typescript
<div className="font-bold text-slate-800 text-base">
  {MOCK_PROJECT_TITLE}  // 始终为 "黄金价格走势分析与投资展望"
  <span className="text-slate-400 font-normal ml-2 text-xs">
    {id || "proj_001"}
  </span>
</div>
```

项目 ID 是正确的（从 URL params 获取），但标题始终是硬编码字符串。

---

### BUG-005 [MEDIUM] "确认进入下一阶段" 按钮不存在

**严重级别**: MEDIUM — 阻塞场景 1.4 和场景 5

**问题描述**:
WorkflowPage 中没有渲染 advance 按钮。测试使用 `page.locator("button", { hasText: "确认进入下一阶段" })` 在所有 WorkflowPage 实例中均未找到该按钮。

---

### BUG-006 [MEDIUM] 无 Agent 输出展示（需求卡片、平台规格、字数计算等）

**严重级别**: MEDIUM

**问题描述**:
由于 WorkflowPage 使用 MOCK_MESSAGES（2 条固定消息），不会显示：
- Phase 0 需求结构化摘要（主题、观点、时长、平台、分类）
- 平台规格参数（B站→1920x1080 8Mbps H.264）
- 目标字数范围（时长×240×语速比）
- 字段确认状态（绿色勾 / 橙色问号）
- 澄清问题列表（clarification_needed）
- Review 审核结果

这些问题在 `src/frontend/components/previews/P0RequirementsView.tsx` 中已有实现，但 WorkflowPage 未使用。

---

### BUG-007 [MEDIUM] 表单提交后不跳转（不稳定复现）

**严重级别**: MEDIUM

**问题描述**:
`CreateProjectForm` 的 `onSubmit` → `useCreateProject.mutate()` 在 API 返回 201 后，`onSuccess` 回调应跳转到 `/projects/:id/phases/0`。但实际测试中发现：
- 部分测试成功跳转
- 部分测试停留在 `/projects/new`

**可能原因**: React Query mutation 的 `onSuccess` 在某些情况下未被触发，或 `apiClient.post` 返回的 Promise 未被正确解析。

---

### BUG-008 [LOW] 阶段标签显示 mock 数据格式

**文件**: `src/frontend/pages/WorkflowPage.tsx:69`
**严重级别**: LOW

```typescript
阶段 {currentPhase}/{PHASE_LABELS.length - 1} · {phaseLabel}
```

显示为 "阶段 0/12 · 需求定义"。阶段从 0 开始计数，但 UI 显示 "N/12" 暗示总共 13 个阶段，有轻微不一致。

---

## 能正常工作的功能

| 功能 | 状态 | 文件 |
|------|------|------|
| 项目列表页加载 | ✅ | ProjectList.tsx |
| "+ 新建项目" 按钮 | ✅ | ProjectList.tsx:73-79 |
| 创建项目表单 (#title, #desc) | ✅ | CreateProjectForm.tsx |
| 描述 < 10 字校验 + 红色提示 | ✅ | CreateProjectForm.tsx:27-29 |
| 标题为空时按钮禁用 | ✅ | CreateProjectForm.tsx:18 |
| 项目列表表格 + 点击跳转 | ✅ | ProjectList.tsx:86-127 |
| ChatInput 组件渲染 | ✅ | ChatInput.tsx |
| TaskCard 组件渲染 | ✅ | TaskCard.tsx |
| ArtifactList 区域可见 | ✅ | ArtifactList.tsx |
| FactualLedger 区域可见 | ✅ | FactualLedger.tsx |
| 后端 API (通过 Vite proxy) | ✅ | vite.config.ts:30-38 |
| 数据库写入 (项目创建) | ✅ | 后端 API |

---

## 根本原因总结

`WorkflowPage.tsx` 当前是一个 **纯 UI 原型**（prototype 风格），所有数据来自 `mockData.ts`，不连接后端 API。核心组件（PhaseNavigation、P0RequirementsView、advance 按钮）未集成。

**Spec 层面的缺失**:
- WorkflowPage 没有 `useProjectState(id)` 调用
- 没有 WebSocket 连接用于实时任务状态更新
- ChatInput 的 `onSend` 没有连接到 IntentRouter API
- 产物预览区没有根据当前 phase 切换对应的 Preview 组件

---

## 修复优先级

| 优先级 | Bug | 影响范围 |
|--------|-----|---------|
| P0 | BUG-001 Mock 数据替换为真实 API | 阻塞所有 Phase 0 场景 |
| P0 | BUG-002 ChatInput 接入后端 | 阻塞对话修改场景 2 |
| P0 | BUG-003 PhaseNavigation 集成 | 阻塞阶段导航 |
| P1 | BUG-005 Advance 按钮 | 阻塞阶段推进 |
| P1 | BUG-006 Agent 输出展示 | 阻塞需求查看 |
| P1 | BUG-004 动态标题 | 影响 UX |
| P2 | BUG-007 提交通道稳定性 | 影响创建流程 |

---

> **测试证据**: 完整 Playwright 测试代码 `tests/e2e/playwright/phase0-manual-scenarios.spec.ts`
> **截图**: `src/frontend/test-results/phase0-*.png`
