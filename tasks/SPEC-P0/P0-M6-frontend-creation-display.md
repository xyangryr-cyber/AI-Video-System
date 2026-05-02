# [SPEC-P0-M6] 前端项目创建与需求展示

## Metadata
- **task_id**: SPEC-P0-M6
- **spec_ref**: Phase0需求.md §2.2, §7; TECH_PLAN_v3.3.md §2, §4
- **depends_on**: [SPEC-P0-M1]
- **priority**: P0
- **estimated_complexity**: L

## Scope
实现前端 `/projects/new` 页面（创建项目表单 + 前端校验）和 `/projects/{id}` 页面（Phase 0 工作区）。工作区包含阶段导航栏、任务清单面板、需求摘要卡片、加载状态指示器、Pre-flight Banner。所有数据通过 REST API 获取。

**业务闭环**: 用户访问页面 → 创建项目 → 看到 Phase 0 工作区（阶段导航 + 任务清单 + 需求摘要卡片 + 加载/错误状态）。

## Allowed Files
- `src/frontend/pages/projects/new.tsx`
- `src/frontend/pages/projects/[id].tsx`
- `src/frontend/components/PhaseNav.tsx`
- `src/frontend/components/TaskList.tsx`
- `src/frontend/components/RequirementsCard.tsx`
- `src/frontend/components/PreflightBanner.tsx`
- `src/frontend/components/LoadingIndicator.tsx`
- `src/frontend/hooks/useProjectState.ts`
- `src/frontend/hooks/usePreflight.ts`
- `src/frontend/types/phase.ts`
- `tests/frontend/test_project_new_page.test.tsx`
- `tests/frontend/test_project_detail_page.test.tsx`
- `tests/frontend/test_requirements_card.test.tsx`

## Forbidden Files
- `src/backend/**`
- `src/shared/**`
- `docs/specs/**`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `/projects/new` 页面渲染标题输入框（单行）+ 描述输入框（多行 textarea）+ 提交按钮
- [ ] AC-2: 标题为空时提交 → 前端阻止提交，显示"标题不能为空"
- [ ] AC-3: 描述 < 10 字时提交 → 前端阻止提交，显示"描述不能少于 10 个字"
- [ ] AC-4: 校验通过后 POST /projects，成功后跳转到 `/projects/{project_id}`
- [ ] AC-5: `/projects/{id}` 页面渲染阶段导航栏：12 个阶段图标；Phase 0 高亮（蓝色），其余灰色
- [ ] AC-6: 阶段导航栏在 Phase 0 完成后图标变为绿色勾
- [ ] AC-7: 页面右侧渲染任务清单面板：显示 task 类型名、状态图标（⏳ pending / 🔄 running / ✅ succeeded / ❌ failed / ⤵ superseded）、持续时间
- [ ] AC-8: generate_artifact running 时任务清单中对应条目显示 🔄 + 持续时间
- [ ] AC-9: review running 时任务清单对应条目显示 🔄 + 持续时间
- [ ] AC-10: 需求摘要卡片渲染：标题/主题/时长/平台（含 specs）/分类/目标字数
- [ ] AC-11: 已确认字段右上角显示绿色勾；待补充字段显示橙色问号
- [ ] AC-12: clarification_needed 非空时卡片渲染"⚠ 需要你补充"区域，列出澄清问题
- [ ] AC-13: RequirementsAgent 运行时对话区底部显示"正在分析你的需求..."加载指示器
- [ ] AC-14: Pre-flight Banner：LLM API 不可用时页面顶部红色 Banner 显示"AI 服务暂不可用"，"+ 新建项目"按钮禁用；后端 API 不可用时全屏错误页面 + 重试按钮；SQLite 异常时黄色 Banner
- [ ] AC-15: 页面首次加载时执行 Pre-flight 检查；`/projects/{id}` 页面每 30s 轮询健康状态

## Verification Commands
```bash
# Frontend unit tests
npx vitest run tests/frontend/test_project_new_page.test.tsx
npx vitest run tests/frontend/test_project_detail_page.test.tsx
npx vitest run tests/frontend/test_requirements_card.test.tsx

# Type check
npx tsc --noEmit

# Lint
npx eslint src/frontend/pages/projects/new.tsx src/frontend/pages/projects/\[id\].tsx src/frontend/components/PhaseNav.tsx src/frontend/components/TaskList.tsx src/frontend/components/RequirementsCard.tsx src/frontend/components/PreflightBanner.tsx
```

## Completion Definition
`/projects/new` 页面表单校验正确，提交后跳转。`/projects/{id}` 页面完整渲染阶段导航、任务清单、需求摘要卡片。任务状态图标和持续时间正确显示。已确认/待补充字段标记正确。Pre-flight Banner 三种状态正确渲染。所有测试通过。

## Test Mapping
| AC | 手动测试场景 | 检查点 |
|---|---|---|
| AC-1 | 场景 1.1 — 进入创建页 | 1.1a-c 标题框/描述框/提交按钮 |
| AC-2, AC-3 | 场景 6.1 — 输入校验 | 6.1 标题空/描述不足被阻止 |
| AC-4, AC-5 | 场景 1.2 — 提交后 | 1.2a 跳转项目页 |
| AC-5 | 场景 1.2 — 阶段导航 | 1.2b Phase 0 高亮 |
| AC-7, AC-8 | 场景 1.2 — 任务清单 | 1.2e generate_artifact 🔄 / review ⏳ |
| AC-13 | 场景 1.2 — 加载指示器 | 1.2d "正在分析你的需求..." |
| AC-10, AC-11 | 场景 1.3 — 需求卡片 | 1.3a-d 字段 + 绿色勾 |
| AC-8, AC-9 | 场景 1.3 — 任务状态 | 1.3e-f 状态更新 |
| AC-7 | 场景 1.4 — 任务完成 | 1.4a review ✅ |
| AC-12 | 场景 3.1 — 澄清区域 | 3.1a-e 澄清问题 + 橙色问号 |
| AC-14 | Pre-flight | 红色 Banner / 黄色 Banner / 全屏错误 |
