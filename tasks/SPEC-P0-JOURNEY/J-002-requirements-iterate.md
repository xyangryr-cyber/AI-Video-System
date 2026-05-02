# SPEC-J-002: 用户修改需求 → 系统重新生成并审核

## Metadata

```yaml
spec_id: SPEC-J-002
delivery_kind: journey
evidence_type: user_observable
parent_journey: null
status: PENDING
owner: TBD
```

## User Behavior (Required)

> 用户在 Phase 0 对话区输入修改意见（如"改成15分钟""从技术角度分析""重新来"）
> → Router 识别意图为 `revise` 或 `regenerate`
> → 等待 ≤60s
> → 对话区追加更新后的需求摘要卡片（被修改字段已更新，澄清问题减少）
> → 任务清单中旧 `review` 标记为 `superseded`，新 `review` 自动创建并执行
> → 若 Router 无法识别意图（置信度 < 0.6），前端显示澄清追问（如"你是想修改需求，还是进入下一阶段？"）

Bad alternative rejected: "Agent 重新生成 JSON" / "task_ledger 状态变更" — 内部行为。

## Evidence (Required)

| Artifact | Path | Required |
|---|---|---|
| Test/recording | `tests/e2e/playwright/phase0-J-002-iterate.spec.ts` | yes |
| Screenshot | `artifacts/J-002/revised-requirements-card.png` | yes |
| Real produced data | `artifacts/J-002/requirements_v2.json` — 必须与 v1 有差异且通过 `assert_artifact.py` | yes |

## Definition of Done

- [ ] Playwright test: 输入 revise 指令 → 卡片更新 → review 重新执行 → 全部 PASS
- [ ] Playwright test: 输入 regenerate 指令 → 卡片从零重建 → review 重新执行 → PASS
- [ ] Playwright test: 输入模糊指令 → Router 返回 clarify → 前端显示澄清追问 → PASS
- [ ] `requirements_v2.json` 通过 placeholder detector
- [ ] 修改后的卡片截图已提交

## Internal Modules Touched

| Module SPEC | Layer (informational) | evidence_type | Status |
|---|---|---|---|
| SPEC-M-006 | backend/engine/router | eval_based | PENDING |
| SPEC-M-007 | backend/agents/CompletenessReviewer | eval_based | PENDING |
| SPEC-M-008 | backend/services (revise/regenerate + artifact versioning) | consumer_driven | PENDING |
| SPEC-M-009 | frontend/components/workflow/ChatInput | user_observable | PENDING |

## Out of Scope

- 首次项目创建和需求生成（→ J-001）
- 用户确认偏好并推进（→ J-003）
- `inject_subtask`（调研子任务）— 一期暂不实现，由 J-002 后续迭代覆盖

## Notes

- 来源：Phase0需求.md §4, §5
- Router 置信度阈值 0.6 来自 §5.1
- revise 触发 artifact_version 自增（§5.3），旧 review → superseded，新 review 自动创建
- 连续 5 次 revise 仍不满意 → 提示改写输入而非继续 regenerate（§1.3 场景卡片）
