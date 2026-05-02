# SPEC-P0-FIX-005: Advance 按钮 + GateKeeper 状态展示

> **来源 Bug**: BUG-005 (advance 按钮不存在)
> **根因**: WorkflowPage 未渲染"确认进入下一阶段"按钮，未集成 GateKeeper 状态检查
> **严重级别**: MEDIUM — 阻塞场景 1.4（审核通过→推进）和场景 5（门禁与推进）
> **依赖**: SPEC-P0-FIX-001（需要项目状态数据）, SPEC-P0-FIX-004（ArtifactModal 中已可查看产物）

---

## 根因分析

后端已实现：
- `POST /api/projects/:id/advance` — 推进到下一阶段（含 GateKeeper 检查）
- `POST /api/projects/:id/chat` — 通过 IntentRouter 检测 advance 意图并返回 `highlight_confirm_button: true`

前端缺失：
- WorkflowPage 无 advance 按钮组件
- 无 GateKeeper 状态展示（通过/阻塞/阻塞原因）
- 无 advance hook（调用 advance API）
- Preferences 弹窗存在但 advance 触发路径不通

**Interaction flow** (spec definition):
1. CompletenessReviewer 输出 PASS → GateKeeper 检查通过 → 按钮变为可点击（高亮）
2. 用户点击"确认进入下一阶段" → 偏好提取弹窗 → 用户确认 → POST /advance
3. GateKeeper 未通过 → 按钮禁用 + 显示阻塞原因

---

## Acceptance Criteria

| # | AC | 验证方式 |
|---|-----|---------|
| AC-1 | WorkflowPage 底部/ChatHistory 下方显示"确认进入下一阶段"按钮 | Playwright: `button:has-text("确认进入下一阶段")` 可见 |
| AC-2 | GateKeeper 未通过时按钮 disabled | Playwright: 新项目刚创建后按钮 disabled |
| AC-3 | 按钮 disabled 时显示阻塞原因 tooltip | Playwright: hover disabled 按钮 → tooltip 显示原因 |
| AC-4 | GateKeeper 通过后按钮变为 enabled（高亮蓝色） | Playwright: review 完成后按钮 enabled |
| AC-5 | 点击 enabled 按钮 → 显示偏好确认弹窗（如有新偏好） | Playwright: 弹窗 "AI 记忆同步中" 出现 |
| AC-6 | 点击"确认并进入下一阶段" → POST /advance → 页面跳转到 Phase 1 | Playwright: URL 变为 `/phases/1` |
| AC-7 | 点击"跳过" → 直接 POST /advance（不确认偏好） | Playwright: 跳过偏好后跳转 |
| AC-8 | advance API 失败时显示错误提示，不跳转 | Playwright: 模拟 API 500 |
| AC-9 | GateKeeper 状态通过 Chat API 的 `highlight_confirm_button` 响应动态更新 | 验证 chat 返回后按钮状态变化 |

---

## TDD 实现计划

### RED 1: Advance 按钮存在性 + 状态测试

```typescript
// tests/unit/frontend/WorkflowPage.test.tsx
// - mock useProjectState: 返回 current_phase=0, gate_status={passed: false}
// - 断言 "确认进入下一阶段" 按钮存在
// - 断言按钮为 disabled 状态
// - mock gate_status.passed=true → 断言按钮 enabled
```

### RED 2: useAdvance hook 测试

```typescript
// tests/unit/frontend/hooks/useAdvance.test.ts
// - useAdvance(id).advance() 调用 POST /api/projects/:id/advance
// - API 返回 { status: "advanced", current_phase: 1 } → resolve
// - API 返回 400/409 (gate blocked) → reject with error
// - isAdvancing 在请求期间为 true
```

### RED 3: Preference modal flow 测试

```typescript
// 测试偏好弹窗交互:
// - 点击 advance 按钮 → modal 出现
// - 点击"确认并进入下一阶段" → advance API 调用
// - 点击"跳过" → 直接 advance API 调用
// - 点击"关闭" → modal 关闭，不调用 advance
```

### GREEN 1: 创建 useAdvance hook

```typescript
// src/frontend/hooks/useAdvance.ts
export function useAdvance(projectId: string) {
  const mutation = useMutation({
    mutationFn: () => apiClient.post(`/api/projects/${projectId}/advance`),
  });
  return { advance: mutation.mutateAsync, isAdvancing: mutation.isPending, error: mutation.error };
}
```

### GREEN 2: Advance 按钮 + GateKeeper 状态

```typescript
// WorkflowPage.tsx
// 1. 使用 useProjectState 获取 gate 状态（或通过 chat API 的 highlight_confirm_button）
// 2. 渲染 AdvanceButton:
//    - gate passed → enabled, 蓝色高亮
//    - gate blocked → disabled, 灰色 + tooltip 显示原因
// 3. onClick → 显示 preference modal
```

### GREEN 3: Preference modal + advance 流程

```typescript
// Advance flow:
// 1. 用户点击按钮
// 2. 检查是否有未确认偏好 → 有则弹出 modal
// 3. 用户确认/跳过 → POST /advance
// 4. onSuccess → navigate(`/projects/${id}/phases/${newPhase}`)
// 5. onError → 显示错误 toast
```

### REFACTOR

- 将 advance 按钮提取为独立组件 `AdvanceButton`（含 GateKeeper 状态展示）
- 将 preference modal 逻辑提取为 hook `usePreferenceGate`

---

## 允许修改的文件

| 文件 | 用途 |
|------|------|
| `src/frontend/pages/WorkflowPage.tsx` | 添加 advance 按钮 |
| `src/frontend/hooks/useAdvance.ts` | **新建** |
| `src/frontend/components/workflow/AdvanceButton.tsx` | **新建** (可选) |
| `tests/unit/frontend/hooks/useAdvance.test.ts` | 新增 |
| `tests/unit/frontend/WorkflowPage.test.tsx` | 更新 |

## 禁止修改的文件

- `src/backend/api/routes/projects.py`（advance API 已实现）
- `src/backend/engine/gatekeeper.py`
- `src/frontend/components/PreferenceWritebackCard.tsx`

---

## 验证命令

```bash
# Hook 测试
cd src/frontend && npx vitest run tests/unit/frontend/hooks/useAdvance.test.ts

# E2E 验证 (Playwright)
# 1. 创建完整描述项目 → 等待 review 完成
# 2. 验证 advance 按钮 enabled
# 3. 点击 → 偏好弹窗出现
# 4. 点击 "确认并进入下一阶段" → 跳转到 Phase 1
# 5. 创建项目后 review 未完成 → 验证按钮 disabled + 原因
```
