# SPEC-P0-FIX-003: PhaseNavigation 集成到 WorkflowPage

> **来源 Bug**: BUG-003 (PhaseNavigation 未渲染)
> **根因**: `PhaseNavigation.tsx` 组件已完整实现但 WorkflowPage 从未导入或使用它
> **严重级别**: HIGH — 用户无法在工作流页面切换阶段
> **依赖**: SPEC-P0-FIX-001（需要 `useProjectState` 的 `current_phase` 数据）

---

## 根因分析

`components/PhaseNavigation.tsx` 已实现：
- 13 个阶段按钮 (P0-P12) + Veritas 事实核查入口
- `data-active` 属性标记当前活跃阶段
- 完成状态绿点指示
- Tooltip 显示阶段名称

但 WorkflowPage.tsx 的 import 列表和 JSX 中均无 PhaseNavigation：

```typescript
// WorkflowPage.tsx — PhaseNavigation 未导入
import { ChatHistory } from "@frontend/components/workflow/ChatHistory"
import { TaskCard } from "@frontend/components/workflow/TaskCard"
import { ChatInput } from "@frontend/components/workflow/ChatInput"
// ❌ 缺: import { PhaseNavigation } from "@frontend/components/PhaseNavigation"
```

---

## Acceptance Criteria

| # | AC | 验证方式 |
|---|-----|---------|
| AC-1 | WorkflowPage 左侧渲染 PhaseNavigation sidebar | Playwright: `[data-testid="phase-nav-sidebar"]` 可见 |
| AC-2 | 当前 phase 的按钮高亮（`data-active="true"`）| Playwright: 验证 `[data-testid="phase-nav-0"]` 的 `data-active="true"` |
| AC-3 | 点击 P0 按钮 → URL 不变（当前已在 P0）| Playwright: 点击 P0 后 URL 不变 |
| AC-4 | 已完成阶段显示绿色圆点指示器 | Playwright: 验证已完成 phase 的 green dot |
| AC-5 | 点击其他 phase → URL 跳转到对应 phase 页面 | Playwright: 点击 P1 后 URL 变为 `/projects/:id/phases/1` |
| AC-6 | `completedPhases` 从 `useProjectState` 数据派生 | 检查: completedPhases = data.phases 中 status=completed 的数量 |
| AC-7 | Veritas 按钮可见（事实核查入口） | Playwright: ShieldCheck 图标可见 |
| AC-8 | Tooltip 在 hover 时显示阶段名 | Playwright: hover P0 按钮 → tooltip 显示 "需求定义" |

---

## TDD 实现计划

### RED 1: PhaseNavigation 存在性测试

```typescript
// tests/unit/frontend/WorkflowPage.test.tsx
// 测试:
// 1. WorkflowPage 渲染 PhaseNavigation
// 2. PhaseNavigation 的 currentPhase prop 来自 useParams
// 3. PhaseNavigation 的 phases prop 来自 useProjectState
// 4. 断言 [data-testid="phase-nav-sidebar"] 在 DOM 中
```

### RED 2: 导航跳转测试

```typescript
// 测试:
// 1. 点击 PhaseNavigation 的 P1 按钮
// 2. 断言 navigate 被调用，路径包含 /phases/1
// 3. 当前 phase 按钮的 data-active="true"
```

### GREEN 1: 最小集成

```typescript
// WorkflowPage.tsx
import { PhaseNavigation } from "@frontend/components/PhaseNavigation"

// 在 JSX 中添加（ChatHistory 左侧）:
<PhaseNavigation
  currentPhase={currentPhase}
  phases={phaseItems}
  completedPhases={completedPhases}
  onSelectPhase={(p) => navigate(`/projects/${id}/phases/${p}`)}
/>

// phaseItems 从 useProjectState 的数据构建
// completedPhases = data.project.latest_reached_phase ?? currentPhase
```

### GREEN 2: 数据映射

```typescript
// 将 useProjectState 返回的 phases 数据映射为 PhaseNavigation 需要的 PhaseItem[] 格式
const phaseItems = (data?.phases ?? []).map(p => ({
  phase: p.phase_index ?? p.phase,
  status: p.status,
  artifact_status: p.artifact_status,
}));
```

### REFACTOR

- 确保 WorkflowPage 的布局在添加 sidebar 后响应式正常（mobile 时隐藏 PhaseNavigation）
- 检查 ArtifactList/PhaseNavigation/主区域的 flex 布局比例

---

## 允许修改的文件

| 文件 | 用途 |
|------|------|
| `src/frontend/pages/WorkflowPage.tsx` | 导入并渲染 PhaseNavigation |
| `tests/unit/frontend/WorkflowPage.test.tsx` | 更新测试 |

## 禁止修改的文件

- `src/frontend/components/PhaseNavigation.tsx`（功能完整）
- `src/frontend/components/workflow/*`

---

## 验证命令

```bash
# 单元测试
cd src/frontend && npx vitest run tests/unit/frontend/WorkflowPage.test.tsx

# E2E 验证 (Playwright)
# 1. 进入任意项目的 Phase 0 页面
# 2. 验证 data-testid="phase-nav-sidebar" 可见
# 3. 验证 data-testid="phase-nav-0" data-active="true"
# 4. hover P0 → tooltip 显示 "需求定义"
# 5. 点击 P1 → URL 跳转到 /phases/1
```
