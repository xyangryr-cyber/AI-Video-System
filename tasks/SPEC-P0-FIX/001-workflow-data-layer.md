# SPEC-P0-FIX-001: WorkflowPage 数据层接入真实 API

> **来源 Bug**: BUG-001 (Mock 数据), BUG-004 (Mock 标题)
> **根因**: WorkflowPage.tsx 从 `mockData.ts` 导入硬编码数据，不调用任何后端 API
> **严重级别**: CRITICAL — 阻塞所有 Phase 0 场景
> **依赖**: 无（这是基础层，其他 SPEC 依赖本 SPEC）

---

## 根因分析

```typescript
// WorkflowPage.tsx:11-17 — 当前状态
import {
  MOCK_CURRENT_TASK_TITLE,
  MOCK_FACTUAL_DATA,
  MOCK_MESSAGES,
  MOCK_PROJECT_TITLE,
  MOCK_TASKS,
} from "@frontend/components/workflow/mockData"
```

`useProjectState(id)` 已存在于 `hooks/useProjectState.ts`，返回 `GET /api/projects/:id/state` 的真实数据。WorkflowPage 已通过 `useParams` 获取 `id`，但从未调用 `useProjectState(id)`。

**为什么 mock 数据在这里**: 提交 `a43048ee [SPEC-E-UI-V2]` 引入了新 WorkflowPage 布局，mock 数据用作 UI 开发的脚手架，但未在后续替换为真实 API。

---

## Acceptance Criteria

| # | AC | 验证方式 |
|---|-----|---------|
| AC-1 | `MOCK_PROJECT_TITLE` 不再被使用；页面标题来自 `useProjectState(id).data.project.title` | Playwright: 创建项目后进入页面，标题匹配用户输入的标题 |
| AC-2 | `MOCK_TASKS` 不再被使用；TaskCard 任务列表来自 `useProjectState(id).data.task_ledger` | Playwright: 验证任务列表条目与后端 task_ledger 一致 |
| AC-3 | `MOCK_MESSAGES` 不再被使用；ChatHistory 消息来自 `useProjectState(id).data.events` 或专用 chat hook | Playwright: 验证新项目对话区为空或有初始化消息 |
| AC-4 | `MOCK_FACTUAL_DATA` 不再被使用；FactualLedger 数据来自真实 API | Playwright: 验证事实核查面板数据与项目关联 |
| AC-5 | `MOCK_CURRENT_TASK_TITLE` 不再被使用；当前任务标题反映 task_ledger 中第一个 active 任务 | Playwright: 验证当前任务标题动态变化 |
| AC-6 | `mockData.ts` 文件不被 WorkflowPage.tsx 导入 | 静态检查: grep MOCK_ pages/WorkflowPage.tsx 无输出 |
| AC-7 | Loading state: 数据加载中显示 LoadingState 组件 | Playwright: 验证加载中状态 |
| AC-8 | Error state: API 失败时显示 ErrorState 组件并支持 retry | Playwright: 验证错误状态 |

---

## TDD 实现计划

### RED 1: 测试 WorkflowPage 使用真实数据而非 mock

```typescript
// tests/unit/frontend/WorkflowPage.test.tsx
// 测试文件: WorkflowPage 渲染时调用 useProjectState
// - mock useProjectState 返回真实数据格式
// - 断言页面标题显示 project.title（而非 MOCK_PROJECT_TITLE）
// - 断言 MOCK_PROJECT_TITLE 的字符串 "黄金价格走势分析与投资展望" 不出现在页面中
```

### RED 2: 测试 task 列表来自 API 数据

```typescript
// 测试文件: WorkflowPage.test.tsx
// - mock useProjectState 返回包含 task_ledger 的数据
// - 断言 TaskCard 显示的 task 条目与 mock 数据一致
// - 断言 MOCK_TASKS 的内容不出现在页面中
```

### RED 3: 测试 loading/error 状态

```typescript
// 测试文件: WorkflowPage.test.tsx
// - mock useProjectState 返回 isLoading=true → 断言 LoadingState 渲染
// - mock useProjectState 返回 isError=true → 断言 ErrorState 渲染
```

### GREEN 1: 最小实现 — 替换标题

```typescript
// WorkflowPage.tsx
// 1. 添加: const { data, isLoading, isError } = useProjectState(id)
// 2. 替换 MOCK_PROJECT_TITLE → data?.project?.title ?? id
// 3. 保留其他 mock 数据（暂时）, 逐步替换
```

### GREEN 2: 替换 task 数据

```typescript
// 将 MOCK_TASKS 替换为从 task_ledger 派生的数据
// Phase 0 默认任务:
//   - generate_artifact (RequirementsAgent)
//   - review (CompletenessReviewer)
// 根据 task_ledger 中的状态决定 completed 布尔值
```

### GREEN 3: 处理 loading/error 状态

```typescript
// 条件渲染: if (isLoading) return <LoadingState />
// if (isError) return <ErrorState message="..." onRetry={refetch} />
```

### REFACTOR

- 清理 `mockData.ts` 中不再使用的导出（保留仍被其他组件使用的部分）
- 提取 `useWorkflowData` hook 封装数据获取逻辑
- 统一 loading/error 状态处理

---

## 允许修改的文件

| 文件 | 用途 |
|------|------|
| `src/frontend/pages/WorkflowPage.tsx` | 主要修改目标 |
| `src/frontend/hooks/useProjectState.ts` | 可能需要增强（如果当前返回数据不完整） |
| `tests/unit/frontend/WorkflowPage.test.tsx` | 新增测试文件 |

## 禁止修改的文件

- `src/frontend/components/workflow/mockData.ts`（只移除导入，不修改文件本身）
- `src/frontend/components/workflow/TaskCard.tsx`
- `src/frontend/components/workflow/ChatHistory.tsx`
- `src/frontend/components/workflow/FactualLedger.tsx`
- `src/backend/**`

---

## 验证命令

```bash
# 前端类型检查
cd src/frontend && npx tsc --noEmit

# 单元测试
cd src/frontend && npx vitest run tests/unit/frontend/WorkflowPage.test.tsx

# E2E 验证 (通过浏览器)
# 1. 创建项目后进入 WorkflowPage
# 2. 标题显示用户输入的项目标题
# 3. 任务卡片显示 generate_artifact/review 任务
# 4. 对话区为空或显示系统初始化消息
```
