# SPEC-J-003: 用户确认偏好 → 门禁校验 → 推进到 Phase 1

## Metadata

```yaml
spec_id: SPEC-J-003
delivery_kind: journey
evidence_type: user_observable
parent_journey: null
status: PENDING
owner: TBD
```

## User Behavior (Required)

> 用户在 Phase 0 项目详情页点击"确认进入下一阶段"按钮
> → (首次) 弹出偏好确认 Modal，展示 Agent 从本阶段对话中提取的候选偏好（含依据/置信度/作用域）
> → 用户对每条偏好：勾选/取消勾选/编辑文字/切换 scope（项目/全局）
> → 点击"保存勾选项并推进"（或"全部接受"/"全部拒绝"）
> → Modal 关闭，GateKeeper 执行 4 项门禁检查
> → 全部 PASS → Phase 0 阶段导航图标变绿色勾，Phase 1 高亮
> → 任一 FAIL → 弹窗显示失败原因，按钮保持禁用

Bad alternative rejected: "FSM.transition(phase_1)" / "preferences 写入 SQLite" — 内部行为。

## Evidence (Required)

| Artifact | Path | Required |
|---|---|---|
| Test/recording | `tests/e2e/playwright/phase0-J-003-gate-advance.spec.ts` | yes |
| Screenshot | `artifacts/J-003/preference-modal.png` | yes |
| Screenshot | `artifacts/J-003/phase1-highlighted.png` | yes |
| Real produced data | `artifacts/J-003/preferences.json` — `preferences_confirmed_at` 非 null | yes |

## Definition of Done

- [ ] Playwright test: 首次点击"确认进入下一阶段" → Modal 弹出 → 用户勾选偏好 → 保存 → GateKeeper PASS → Phase 1 高亮
- [ ] Playwright test: 再次点击 → 跳过偏好提取 → 直接 GateKeeper → PASS
- [ ] Playwright test: nothing_found → Modal 显示"未发现新偏好" → 用户点"跳过" → 推进
- [ ] Playwright test: GateKeeper FAIL（如 review 未 PASS）→ 弹窗显示阻塞原因 → 按钮保持禁用
- [ ] `preferences.json` 中 `preferences_confirmed_at` 非 null

## Internal Modules Touched

| Module SPEC | Layer (informational) | evidence_type | Status |
|---|---|---|---|
| SPEC-M-010 | backend/agents/PreferenceExtractor | eval_based | PENDING |
| SPEC-M-011 | backend/engine/gatekeeper | consumer_driven | PENDING |
| SPEC-M-012 | backend/api (advance + preferences endpoints) | consumer_driven | PENDING |
| SPEC-M-013 | frontend/components/PreferenceModal | user_observable | PENDING |
| SPEC-M-014 | frontend/components/AdvanceButton | user_observable | PENDING |

## Out of Scope

- Phase 1 及之后的阶段推进（每个阶段有自己的 Gate）
- Preference 在后续阶段的自动注入（→ SPEC-D pipeline phases）
- GateKeeper 之外的 FSM 完整状态机（→ SPEC-C backend core）

## Notes

- 来源：Phase0需求.md §6, §7.4
- Gate 0 四项门禁：产物完整性 / 审核通过 / 无进行中任务 / 偏好确认完成（§6.2）
- PreferenceExtractor 不在 task_ledger 中，由 API 层同步调用（§6.3）
- `nothing_found: true` 时仍需用户显式点击"跳过"（§6.4）
- 全局偏好写 `user_preferences_md`，项目偏好写 `project_preferences_md`
