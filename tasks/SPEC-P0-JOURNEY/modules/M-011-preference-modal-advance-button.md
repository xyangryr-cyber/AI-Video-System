# SPEC-M-011: Preference Modal + Advance Button UI

## Metadata

```yaml
spec_id: SPEC-M-011
delivery_kind: module
parent_journey: SPEC-J-003
evidence_type: user_observable
status: PENDING
allowed_files:
  - "src/frontend/components/workflow/PreferenceModal.tsx"
  - "src/frontend/components/workflow/AdvanceButton.tsx"
forbidden_files: ["HARNESS.md", "CLAUDE.md", ".claude/**"]
```

## Why This Module Exists

偏好确认 Modal 和"确认进入下一阶段"按钮是用户推进流程的 UI 入口。Modal 展示 Agent 提取的候选偏好（含依据/置信度/作用域），用户可逐条审核（勾选/编辑/切换 scope）。AdvanceButton 的状态由 GateKeeper 条件实时驱动：条件全满足时高亮可点击，否则灰色禁用并显示原因。两者共同构成从"用户意图推进"到"系统确认推进"的完整 UI 闭环。

## Consumer / Evidence

### evidence_type: user_observable

| Field | Value |
|---|---|
| Closed by journey | SPEC-J-003（journey 的 playwright test 覆盖 Modal + Button） |
| Note | 此模块不运行独立的 user-observable 测试 |

## Interfaces

| name | params | returns | raises | example |
|---|---|---|---|---|
| `PreferenceModal` | `candidates: Candidate[], onConfirm: (selected) => void, onReject: () => void` | React component | — | 模态对话框 |
| `AdvanceButton` | `projectId: string, gateStatus: GateStatus` | React component | — | 对话区底部按钮 |

## Data Constraints

| target | rules |
|---|---|
| Modal 默认状态 | 所有候选偏好默认勾选 |
| 单条操作 | 勾选/取消勾选/编辑文字（内联 input）/切换 scope（radio: 项目/全局） |
| 全部接受 | 所有条目保持勾选 → POST preferences/confirm → 关闭 Modal → 重新 POST advance |
| 全部拒绝 | candidates 传空数组 → POST preferences/confirm → preferences_confirmed_at = now() → 推进 |
| nothing_found | Modal 内容="本阶段未发现新的偏好规则。"，按钮="跳过" |
| AdvanceButton 启用条件 | GateKeeper 4 项全部满足 → 高亮蓝色可点击 |
| AdvanceButton 禁用 | 任一项不满足 → 灰色 + tooltip 显示原因 |

## Exception Handling

| scenario | trigger | expected |
|---|---|---|
| 用户关闭 Modal 不操作 | 点击 Modal 外部或按 Esc | Modal 关闭，preferences_confirmed_at 保持 null；下次点击按钮重新触发偏好流程 |
| API 调用失败（保存偏好时） | POST preferences/confirm 返回 500 | Modal 内显示错误提示"保存失败，请重试"，不关闭 Modal |
| GateKeeper FAIL 后重试 | 用户等待 task 完成后再次点击 | 按钮自动重新检查条件，满足后变为可用 |

## Verification Commands

- `npx vitest run tests/unit/frontend/workflow/AdvanceButton.test.tsx`
- `npx playwright test tests/e2e/playwright/phase0-J-003-gate-advance.spec.ts`

## Definition of Done

- [ ] 首次点击 → Modal 弹出 → 展示候选偏好（含依据/置信度/scope）
- [ ] 用户编辑偏好文字 + 切换 scope → 保存 → 写入正确
- [ ] 全部接受 → 推进
- [ ] 全部拒绝 → 推进（无偏好写入）
- [ ] nothing_found → "跳过" → 推进
- [ ] GateKeeper FAIL → 按钮禁用 + 显示原因
- [ ] GateKeeper PASS → 按钮高亮可点击 → Phase 1 高亮
- [ ] Parent journey SPEC-J-003 playwright test 通过
