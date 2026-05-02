# [SPEC-P0-M7] 前端对话交互与门禁界面

## Metadata
- **task_id**: SPEC-P0-M7
- **spec_ref**: Phase0需求.md §5, §6.4, §7.4; TECH_PLAN_v3.3.md §2, §3.1
- **depends_on**: [SPEC-P0-M6]
- **priority**: P0
- **estimated_complexity**: L

## Scope
实现项目详情页的对话交互区和门禁推进 UI。对话区渲染用户消息和 Agent 回复卡片，支持 revise/regenerate/clarify 流程的 UI 更新。偏好确认 Modal（含编辑/接受/拒绝/nothing_found 状态）。"确认进入下一阶段"按钮（高亮/禁用双态 + 原因提示）。阶段推进后 UI 过渡。

**业务闭环**: 用户对话输入 → 看到 Agent 回复 + 需求卡片更新 → 偏好确认 Modal → 点击推进按钮 → Phase 0 完成，进入 Phase 1。

## Allowed Files
- `src/frontend/components/DialogueArea.tsx`
- `src/frontend/components/ChatInput.tsx`
- `src/frontend/components/PreferenceModal.tsx`
- `src/frontend/components/AdvanceButton.tsx`
- `src/frontend/components/AgentActivityPanel.tsx`
- `src/frontend/hooks/useDialogue.ts`
- `src/frontend/hooks/usePreferences.ts`
- `src/frontend/hooks/useAdvance.ts`
- `tests/frontend/test_dialogue.test.tsx`
- `tests/frontend/test_preference_modal.test.tsx`
- `tests/frontend/test_advance_button.test.tsx`

## Forbidden Files
- `src/backend/**`
- `src/shared/**`
- `docs/specs/**`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: 对话区渲染用户消息列表 + Agent 回复卡片，新消息自动滚动到底部
- [ ] AC-2: 项目创建后对话区顶部显示用户刚提交的标题和描述作为第一条消息
- [ ] AC-3: 需求摘要卡片在 revise/regenerate 后增量更新（字段变化高亮过渡）
- [ ] AC-4: 用户输入 revise 后：对话区追加用户消息 → user_revision task 出现 → 完成后需求卡片更新 → artifact_version 显示变化 → 旧 review 标记 superseded → 新 review 出现
- [ ] AC-5: 用户输入 regenerate 后：对话区追加用户消息 → 新 generate_artifact task → 全新需求卡片
- [ ] AC-6: 用户输入模糊意图后：Agent 回复澄清问题（"你是想修改需求，还是进入下一阶段？"）；连续 2 次 clarify 后显示 4 个候选动作按钮（修改需求/重新生成/查资料/进入下一步）
- [ ] AC-7: 偏好确认 Modal 渲染：标题"本阶段学到的偏好"、candidates 列表（每条含 rule/evidence/scope 切换）、默认全部勾选
- [ ] AC-8: Modal 内用户可：勾选/取消勾选单条、点击"编辑"内联编辑文字、切换 scope（仅本项目/所有项目）
- [ ] AC-9: "全部接受"→ 提交全部 candidates → preferences_confirmed_at 写入 → 关闭 Modal → 自动重新调用 advance
- [ ] AC-10: "全部拒绝"→ 提交空 candidates → preferences_confirmed_at 写入 → 关闭 Modal → 自动重新调用 advance
- [ ] AC-11: "保存勾选项并推进"→ 仅提交勾选的 candidates → 同 AC-9
- [ ] AC-12: nothing_found 时 Modal 内容替换为"本阶段未发现新的偏好规则"，底部按钮变为"跳过"
- [ ] AC-13: "确认进入下一阶段"按钮在 GateKeeper 条件全部满足时高亮可点击；条件不满足时灰色禁用 + 旁显示原因
- [ ] AC-14: 用户点击高亮按钮 → API 调用 → 成功后 Phase 0 阶段导航图标变绿色勾、Phase 1 高亮
- [ ] AC-15: Agent 活动流面板显示 Router 识别动作（revise/regenerate/clarify 等）

## Verification Commands
```bash
# Dialogue component tests
npx vitest run tests/frontend/test_dialogue.test.tsx

# Preference modal tests
npx vitest run tests/frontend/test_preference_modal.test.tsx

# Advance button tests
npx vitest run tests/frontend/test_advance_button.test.tsx

# Type check
npx tsc --noEmit

# Lint
npx eslint src/frontend/components/DialogueArea.tsx src/frontend/components/ChatInput.tsx src/frontend/components/PreferenceModal.tsx src/frontend/components/AdvanceButton.tsx
```

## Completion Definition
对话区正确渲染所有消息类型，revise/regenerate/clarify 流程 UI 更新正确。偏好确认 Modal 全部交互路径（接受/拒绝/编辑/跳过）正确执行。"确认进入下一阶段"按钮双态正确。阶段推进后 UI 过渡正确。全部测试通过。

## Test Mapping
| AC | 手动测试场景 | 检查点 |
|---|---|---|
| AC-1, AC-2 | 场景 1.2 — 对话区首条消息 | 1.2c 标题和描述 |
| AC-4 | 场景 2.1 — revise UI | 2.1a 用户消息出现 |
| AC-4 | 场景 2.1 — task 状态 | 2.1b user_revision 🔄 |
| AC-15 | 场景 2.1 — Router 识别 | 2.1c 活动流 revise |
| AC-4 | 场景 2.1 — 字段更新 | 2.1d-f 卡片更新 + superseded |
| AC-4 | 场景 2.2 — 平台变更 | 2.2a-d 平台/版本更新 |
| AC-5 | 场景 2.3 — regenerate UI | 2.3a-e 新卡片 + 版本 + superseded |
| AC-6 | 场景 2.4 — clarify UI | 2.4a-c 澄清回复 + 候选按钮 |
| AC-3 | 场景 3.2 — 卡片增量更新 | 3.2a-c 字段更新 + 标记变化 |
| AC-7, AC-8 | 场景 4.2 — 偏好 Modal | 4.2a-c 列表 + 编辑 + scope |
| AC-9, AC-11 | 场景 4.3 — 编辑+确认 | 4.3a-b 编辑 + 保存推进 |
| AC-13, AC-14 | 场景 1.4 — 按钮可用 | 1.4b-c 高亮可点击 |
| AC-13 | 场景 3.3 — 补充后可用 | 3.3c 按钮可点击 |
| AC-14 | 场景 4.4 — 推进成功 | 4.4a-c Phase 0 勾 + Phase 1 高亮 |
