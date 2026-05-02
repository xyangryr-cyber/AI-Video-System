# SPEC-M-007: Revise/Regenerate Flow + Artifact Versioning

## Metadata

```yaml
spec_id: SPEC-M-007
delivery_kind: module
parent_journey: SPEC-J-002
evidence_type: consumer_driven
status: PENDING
allowed_files:
  - "src/backend/services/artifact_service.py"
  - "src/backend/engine/workflow_engine.py"
forbidden_files: ["HARNESS.md", "CLAUDE.md", ".claude/**"]
```

## Why This Module Exists

此模块管理 revise/regenerate 的完整生命周期：(1) 接收 Router 输出的 action，(2) 根据 action 类型调用 RequirementsAgent.generate 或 RequirementsAgent.revise，(3) artifact_version 自增，(4) 旧 review → superseded，(5) 自动追加新 review 任务。这些步骤的顺序和原子性直接决定数据一致性——如果旧 review 未 superseded 而新 review 已创建，task_ledger 将出现两个 active review。

## Consumer / Evidence

### evidence_type: consumer_driven

| Field | Value |
|---|---|
| Concrete consumer | SPEC-M-008 (ChatInput 触发 revise/regenerate)；SPEC-J-002 (playwright test 验证) |
| Verification command | `pytest tests/integration/test_revise_regenerate_flow.py -v` |
| Non-placeholder check | `python scripts/assert_artifact.py --phase 0 --check "artifact_version>=2,old_review:superseded,new_review:exists"` |

## Interfaces

| name | params | returns | raises | example |
|---|---|---|---|---|
| `WorkflowEngine.handle_user_action(project_id, action, message)` | `project_id: str, action: ActionEnum, message: str` | `TaskLedgerUpdate` | `InvalidActionError` | — |

## Data Constraints

| target | rules |
|---|---|
| artifact_version | 每次 revise/regenerate 后自增（v1 → v2 → ...） |
| 旧 review task | status → `superseded`（不可逆终态） |
| 新 review task | type=`review`, agent=`CompletenessReviewer`, depends_on=刚完成的 task, status=`pending`（自动入队） |
| revise vs regenerate | revise：以原 JSON + 用户消息为输入（增量修改）；regenerate：废弃当前产物，从零重新生成 |

## Exception Handling

| scenario | trigger | expected |
|---|---|---|
| 连续 5 次 revise 仍 FAIL | review 连续 5 次 verdict = FAIL | 系统提示"建议修改原始描述后重新创建项目，而非继续修改"，不继续第 6 次 regenerate |
| 并发 revise | 两次 revise 几乎同时触发 | task_ledger 的 depends_on 链保证顺序执行；后到达的排在当前 running task 之后 |
| revise 后产物与 v1 相同 | LLM 未做任何修改 | artifact_version 仍自增，review 重新执行（防止 LLM 非确定性导致的不一致） |

## Verification Commands

- `pytest tests/integration/test_revise_regenerate_flow.py::test_revise_updates_artifact -v`
- `pytest tests/integration/test_revise_regenerate_flow.py::test_regenerate_creates_new_artifact -v`
- `pytest tests/integration/test_revise_regenerate_flow.py::test_old_review_superseded -v`
- `pytest tests/integration/test_revise_regenerate_flow.py::test_auto_create_new_review -v`

## Definition of Done

- [ ] revise 后 artifact_version 自增，旧 review superseded，新 review 自动创建
- [ ] regenerate 后 artifact 从零重建，版本链正确
- [ ] 连续 5 次 FAIL 后系统阻止继续 regenerate
- [ ] 并发 revise 正确处理（无重复 review）
- [ ] Parent journey SPEC-J-002 playwright test 通过
