# SPEC-J-001: 用户创建项目 → 系统自动生成结构化视频需求

## Metadata

```yaml
spec_id: SPEC-J-001
delivery_kind: journey
evidence_type: user_observable
parent_journey: null
status: PENDING
owner: TBD
```

## User Behavior (Required)

> 用户访问 `/projects/new` → 输入标题(非空)和自然语言描述(≥10字) → 点击"提交"按钮
> → 页面跳转到 `/projects/{id}` → 等待 ≤60s
> → 对话区渲染需求摘要卡片（标题/主题/时长范围/平台/分类/澄清问题列表）
> → 右侧任务清单显示 `generate_artifact`=✅, `review`=🔄 或 ✅
> → 底部输入框可用

Bad alternative rejected: "系统加载配置文件" / "Agent 输出 JSON" — 这些都是内部行为，用户看不到。

## Evidence (Required)

| Artifact | Path | Required |
|---|---|---|
| Test/recording | `tests/e2e/playwright/phase0-J-001-create-generate.spec.ts` | yes |
| Screenshot | `artifacts/J-001/requirements-card.png` | yes |
| Real produced data | `artifacts/J-001/requirements.json` — 必须通过 `assert_artifact.py --phase 0 --check fields:title,topic,target_duration_minutes,platform,category` | yes |

## Definition of Done

- [ ] Playwright test PASSES on real run
- [ ] `requirements.json` 通过 placeholder detector
- [ ] All Internal Modules below are CLOSED
- [ ] 需求摘要卡片截图已提交到 `artifacts/J-001/`

## Internal Modules Touched

| Module SPEC | Layer (informational) | evidence_type | Status |
|---|---|---|---|
| SPEC-M-001 | backend/api + models | consumer_driven | PENDING |
| SPEC-M-002 | backend/agents/RequirementsAgent | eval_based | PENDING |
| SPEC-M-003 | shared/schemas/requirements.json | consumer_driven | PENDING |
| SPEC-M-004 | frontend/pages/NewProject | user_observable | PENDING |
| SPEC-M-005 | frontend/pages/WorkflowPage (Phase 0 view) | user_observable | PENDING |

## Out of Scope

- 用户修改需求（→ J-002）
- 用户确认偏好并推进到 Phase 1（→ J-003）
- Pre-flight 健康检查（→ M-001 module 内部处理）
- 服务重启/浏览器关闭后恢复（→ M-001 module 内部处理）

## Notes

- 来源：Phase0需求.md §1-3, §7.3, §8, §14
- 关联 BDD：`docs/BDD_phase_0_requirements_definition.feature.md`
- RequirementsAgent 的 LLM 调用通过 LiteLLM + Instructor 强制结构化输出
