# SPEC-M-003: NewProject Page + Form Validation

## Metadata

```yaml
spec_id: SPEC-M-003
delivery_kind: module
parent_journey: SPEC-J-001
evidence_type: user_observable
status: PENDING
allowed_files:
  - "src/frontend/pages/NewProject.tsx"
  - "src/frontend/hooks/useCreateProject.ts"
forbidden_files: ["HARNESS.md", "CLAUDE.md", ".claude/**"]
```

## Why This Module Exists

NewProject 页面是 Phase 0 的用户入口。用户在此输入标题和描述，前端校验通过后调用 `POST /projects`，成功后跳转到项目详情页。前端校验（标题非空、描述≥10字）在发 API 请求前执行，减少无效请求。

## Consumer / Evidence

### evidence_type: user_observable

| Field | Value |
|---|---|
| Closed by journey | SPEC-J-001（journey 的 playwright test 覆盖此模块） |
| Note | 此模块不运行独立的 user-observable 测试；依赖 parent journey 的 playwright test |

## Interfaces

| name | params | returns | raises | example |
|---|---|---|---|---|
| `NewProject` page | — | React component | — | 路由 `/projects/new` |
| `useCreateProject` hook | — | `{createProject, isLoading, error}` | — | 调用 `POST /projects` |

## Data Constraints

| target | rules |
|---|---|
| 标题 input | 非空；trim 后长度 > 0 |
| 描述 textarea | ≥ 10 字（trim 后）；中文按字符数计 |
| 提交按钮 | 校验失败时 disabled；提交中显示 loading |
| 错误提示 | 标题空："标题不能为空"；描述不足："描述不能少于 10 个字" |

## Exception Handling

| scenario | trigger | expected |
|---|---|---|
| 标题为空 | 用户点击提交时 title.trim() === "" | 阻止提交，input 下方红色提示"标题不能为空" |
| 描述不足 10 字 | 用户点击提交时 description.trim().length < 10 | 阻止提交，textarea 下方红色提示"描述不能少于 10 个字" |
| API 返回 503 | LLM 不可用 | 页面顶部红色 Banner "AI 服务暂不可用，请稍后重试"；提交按钮禁用 |
| API 网络错误 | fetch 失败 | Toast 提示"网络连接失败，请检查网络后重试" |

## Verification Commands

- `npx vitest run tests/unit/frontend/pages/NewProject.test.tsx`
- `npx playwright test tests/e2e/playwright/phase0-J-001-create-generate.spec.ts`

## Definition of Done

- [ ] 标题空 → 阻止提交 + 显示错误提示
- [ ] 描述 < 10 字 → 阻止提交 + 显示错误提示
- [ ] 合法输入 → POST /projects 调用成功 → 跳转到 /projects/{id}
- [ ] LLM 不可用时 → 红色 Banner + 按钮禁用
- [ ] Parent journey SPEC-J-001 playwright test 通过
