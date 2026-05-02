# SPEC-P0-FIX-006: 修复 CreateProjectForm 提交后导航不可靠

> **来源 Bug**: BUG-007 (表单提交后不跳转，不稳定复现)
> **根因**: React Query mutation 的 `onSuccess` 回调在部分情况下未触发，或 API 响应解析失败导致 Promise rejection
> **严重级别**: MEDIUM — 影响项目创建流程可靠性
> **依赖**: 无

---

## 根因分析

当前创建流程：

```
CreateProjectForm.onSubmit
  → mutation.mutate(input, { onSuccess: (data) => nav(...) })
    → apiClient.post("/api/projects", input)
      → fetch("/api/projects", { method: "POST", body: JSON.stringify(input) })
        → Vite proxy → localhost:8000
```

Playwright 诊断测试发现：
- `POST /api/projects` 请求被发出（通过 `page.on("request")` 捕获）
- 后端确实创建了项目（通过后续 GET 验证数据库中有新记录）
- 但 Playwright 的 `page.on("response")` 未捕获到响应（Vite proxy 响应未被 Playwright 网络层捕获）
- `mutation.onSuccess` 有时触发跳转，有时不触发

**可能的根因**：
1. Vite proxy 在处理 POST 响应时可能触发 CORS 或 content-type 问题，导致浏览器的 `fetch` Promise rejection
2. `apiClient.post` 中的 `res.json()` 解析失败（后端返回格式不一致）
3. React Query `onSuccess` 必须在 `mutate` 的 options 中传入，而非 `useMutation` 的 config（这取决于 react-query v5 的 API 用法）

---

## Acceptance Criteria

| # | AC | 验证方式 |
|---|-----|---------|
| AC-1 | 表单提交后 100% 跳转到项目页（连续 10 次创建） | Playwright: 循环创建 10 次，每次验证跳转 |
| AC-2 | 后端返回非 201 时（4xx/5xx），显示错误提示留在表单页 | Playwright: 模拟后端 500 |
| AC-3 | 导航未发生时（网络超时等），表单页显示错误提示并提供重试 | Playwright: 模拟网络超时 |
| AC-4 | mutation.isPending 期间提交按钮显示 "创建中..." 且 disabled | Playwright: 点击提交后立即检查按钮状态 |

---

## TDD 实现计划

### RED 1: CreateProjectForm 成功场景测试

```typescript
// tests/unit/frontend/components/CreateProjectForm.test.tsx
// - render CreateProjectForm
// - fill title + desc
// - click submit
// - assert onSubmit called with { title, description }
// - assert submit button shows "创建中..." while isSubmitting=true
```

### RED 2: useCreateProject 可靠性测试

```typescript
// tests/unit/frontend/hooks/useCreateProject.test.ts
// - mock apiClient.post to resolve with { id: 'proj_001' }
// - call mutation.mutateAsync
// - assert resolved value === mock response
// - assert onSuccess callback called
//
// - mock apiClient.post to reject with Error
// - assert onError callback called
```

### GREEN 1: 修复 — 检查 apiClient 的 201 响应处理

```typescript
// src/frontend/api/client.ts
// 检查对 HTTP 201 的响应处理:
// 当前逻辑: if (res.status === 204) return undefined; return res.json()
// 201 应该走 res.json() — 确认 201 body 确实是有效 JSON
// 如果后端返回的 Content-Type 不是 application/json，Vite proxy 可能改变它
```

### GREEN 2: 修复 — 确保 onSuccess 在 mutationFn 成功时触发

```typescript
// src/frontend/pages/NewProject.tsx
// React Query v5: onSuccess 应该在 useMutation 的 options 中定义
// 当前写法: mutation.mutate(input, { onSuccess: ... })
// 这种写法在 v5 中有效，但要确保 apiClient.post 正常 resolve
```

### GREEN 3: 添加重试和超时处理

```typescript
// src/frontend/hooks/useCreateProject.ts
// 添加 retry: 0 (创建操作不应自动重试)
// 添加超时处理: AbortController + setTimeout
// onError 中显示 toast 错误提示
```

### REFACTOR

- 统一项目中所有 mutation 的 error handling 模式
- 添加 API 响应格式验证（检查返回的 JSON 是否含 `id` 字段）

---

## 允许修改的文件

| 文件 | 用途 |
|------|------|
| `src/frontend/hooks/useCreateProject.ts` | 增强错误处理和可靠性 |
| `src/frontend/api/client.ts` | 检查 201 响应处理 |
| `src/frontend/pages/NewProject.tsx` | 添加错误展示 |
| `tests/unit/frontend/hooks/useCreateProject.test.ts` | 新增 |
| `tests/unit/frontend/components/CreateProjectForm.test.tsx` | 新增 |

## 禁止修改的文件

- `src/backend/api/routes/projects.py`（创建 API 已正常工作）
- `src/frontend/components/CreateProjectForm.tsx`（校验逻辑正常）

---

## 验证命令

```bash
# 单元测试
cd src/frontend && npx vitest run tests/unit/frontend/hooks/useCreateProject.test.ts
cd src/frontend && npx vitest run tests/unit/frontend/components/CreateProjectForm.test.tsx

# E2E 验证 (Playwright)
# 1. 连续创建 10 个项目
# 2. 验证每次提交后都跳转到 /projects/proj_xxx/phases/0
# 3. 记录任何未跳转的情况
# 4. 模拟后端不可用 → 验证错误展示
```
