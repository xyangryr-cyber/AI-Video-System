# SPEC-M-004: Phase 0 Workflow View (需求卡片 + 任务清单)

## Metadata

```yaml
spec_id: SPEC-M-004
delivery_kind: module
parent_journey: SPEC-J-001
evidence_type: user_observable
status: PENDING
allowed_files:
  - "src/frontend/pages/WorkflowPage.tsx"
  - "src/frontend/components/workflow/RequirementsCard.tsx"
  - "src/frontend/components/workflow/TaskList.tsx"
forbidden_files: ["HARNESS.md", "CLAUDE.md", ".claude/**"]
```

## Why This Module Exists

项目创建后用户看到的是 Phase 0 WorkflowPage 默认视图。此模块包含三个核心 UI 区域：(1) 阶段导航栏 — Phase 0 高亮，(2) 需求摘要卡片 — 展示结构化需求 + 澄清问题 + 快捷选项，(3) 右侧任务清单 — 实时显示 generate_artifact/review 状态。三者的实时更新（WebSocket/轮询）确保用户看到的是当前真实状态。

## Consumer / Evidence

### evidence_type: user_observable

| Field | Value |
|---|---|
| Closed by journey | SPEC-J-001（journey 的 playwright test 覆盖所有三个 UI 区域） |
| Note | 此模块不运行独立的 user-observable 测试 |

## Interfaces

| name | params | returns | raises | example |
|---|---|---|---|---|
| `WorkflowPage` (Phase 0 view) | `projectId: string` | React component | — | 路由 `/projects/{id}` |
| `RequirementsCard` | `requirements: RequirementsOutput, clarification: string[]` | React component | — | 渲染需求摘要 + 澄清问题 |
| `TaskList` | `tasks: TaskLedgerItem[]` | React component | — | 右侧面板任务清单 |

## Data Constraints

| target | rules |
|---|---|
| 需求摘要卡片 | 展示字段：标题/主题/时长/平台(含specs)/分类/目标字数；已确认字段绿色勾，待补充字段橙色问号 |
| 澄清问题区 | clarification_needed 非空时渲染；每个问题附带快捷选项按钮 + 自定义输入 |
| 任务清单 | 初始 2 个任务；状态图标：⏳pending → 🔄running(含耗时) → ✅succeeded/❌failed |
| 实时更新 | WebSocket 或 2s 轮询；状态变更后 ≤ 2s 反映在 UI |

## Exception Handling

| scenario | trigger | expected |
|---|---|---|
| RequirementsAgent 运行中 | generate_artifact status = running | 对话区底部 "正在分析你的需求..." 加载指示器；任务清单对应条目 🔄 + 旋转图标 |
| review FAIL | CompletenessReviewer verdict = FAIL | 任务清单 review 条目 ❌ failed（红色）；卡片底部显示 FAIL 原因 |
| requirements.json 不存在 | 项目刚创建尚未生成 | 卡片区显示 skeleton/placeholder，任务清单显示 pending |
| WebSocket 断开 | 连接丢失 | 自动降级为 5s 轮询；连接恢复后切回 WebSocket |

## Verification Commands

- `npx vitest run tests/unit/frontend/workflow/WorkflowPage.test.tsx`
- `npx playwright test tests/e2e/playwright/phase0-J-001-create-generate.spec.ts`

## Definition of Done

- [ ] 需求摘要卡片正确渲染所有字段（含已确认/待补充状态）
- [ ] 澄清问题列表渲染 + 快捷选项可点击
- [ ] 任务清单实时更新（pending → running → succeeded/failed）
- [ ] 加载指示器在 Agent 运行时显示
- [ ] review FAIL 时红色标注 + 原因展示
- [ ] Parent journey SPEC-J-001 playwright test 通过
