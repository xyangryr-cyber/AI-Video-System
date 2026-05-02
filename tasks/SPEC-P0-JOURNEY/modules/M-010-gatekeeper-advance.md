# SPEC-M-010: GateKeeper + Advance Endpoint + Preferences Persistence

## Metadata

```yaml
spec_id: SPEC-M-010
delivery_kind: module
parent_journey: SPEC-J-003
evidence_type: consumer_driven
status: PENDING
allowed_files:
  - "src/backend/engine/gatekeeper.py"
  - "src/backend/api/routes/projects.py"
  - "src/backend/models/preferences.py"
forbidden_files: ["HARNESS.md", "CLAUDE.md", ".claude/**"]
```

## Why This Module Exists

此模块是 Phase 0 的最后一道关卡——将偏好确认、门禁校验、FSM 推进三个环节串联为原子操作。(1) GateKeeper 是纯函数校验模块（非 LLM Agent，零 token 成本），执行 4 项程序化门禁检查。(2) `POST /projects/{id}/advance` 处理偏好确认流程（首次触发 PreferenceExtractor → 用户确认 → 写入 preferences 表）和 GateKeeper 校验。(3) `POST /projects/{id}/preferences/confirm` 将用户确认的偏好按 scope 写入 `project_preferences_md` 或 `user_preferences_md`，并记录 `preferences_confirmed_at` 时间戳。

## Consumer / Evidence

### evidence_type: consumer_driven

| Field | Value |
|---|---|
| Concrete consumer | SPEC-M-011 (AdvanceButton 调用 advance endpoint)；SPEC-J-003 (playwright test 端到端验证) |
| Verification command | `pytest tests/integration/test_gate_advance.py -v` |
| Non-placeholder check | `python scripts/assert_artifact.py --phase 0 --check "preferences_confirmed_at:non_null,phase_0_status:done,phase_1_status:active"` |

## Interfaces

| name | params | returns | raises | example |
|---|---|---|---|---|
| `POST /projects/{id}/advance` | `project_id: str` | `AdvanceResult {status: "advanced"\|"blocked"\|"confirm_preferences", next_phase?: int, reasons?: str[], candidates?: Candidate[]}` | 404, 409 (有进行中任务) | — |
| `POST /projects/{id}/preferences/confirm` | `project_id: str, candidates: Candidate[]` | `{preferences_confirmed_at: str}` | 404 | — |
| `GateKeeper.check(project_id)` | `project_id: str` | `GateResult {pass: bool, checks: CheckResult[]}` | — | 纯函数，4 项检查 |

## Data Constraints

| target | rules |
|---|---|
| Gate 0 四项门禁 | (1) requirements.json 存在且 JSON Schema 通过 (2) review verdict = PASS (3) task_ledger 所有 task 处于终态 (4) preferences_confirmed_at 非空 |
| preferences 表写入 | scope=`project` → project_preferences_md；scope=`global` → user_preferences_md |
| preferences_confirmed_at | 首次非 null 时间戳；后续推进跳过偏好提取 |
| FSM transition | GateKeeper PASS → phase_0.status = `done` → phase_1.status = `active` → projects.current_phase = 1 |

## Exception Handling

| scenario | trigger | expected |
|---|---|---|
| 产物不存在 | requirements.json 缺失或 JSON 解析失败 | GateKeeper check #1 FAIL → `{status: "blocked", reasons: ["主产物生成失败，请手动重试或调整参数"]}` |
| review 未 PASS | CompletenessReviewer verdict = FAIL | GateKeeper check #2 FAIL → 列出具体阻塞项 |
| 有进行中任务 | task_ledger 存在非终态 task | GateKeeper check #3 FAIL → `"仍有任务正在执行中，请等待完成"` |
| 偏好未确认 | preferences_confirmed_at == null | 不经过 GateKeeper，API 返回 `{action: "confirm_preferences", candidates: [...]}` 触发 Modal |
| 并发 advance | 两次 advance 几乎同时 | 第二次返回 409（第一次已在处理中） |

## Verification Commands

- `pytest tests/integration/test_gate_advance.py::test_gate_all_pass -v`
- `pytest tests/integration/test_gate_advance.py::test_gate_blocked_by_review_fail -v`
- `pytest tests/integration/test_gate_advance.py::test_gate_blocked_by_running_task -v`
- `pytest tests/integration/test_gate_advance.py::test_preferences_first_time_flow -v`
- `pytest tests/integration/test_gate_advance.py::test_preferences_skip_second_time -v`
- `sqlite3 data/db/test.sqlite3 "SELECT status FROM phases WHERE project_id='test' AND phase_number=0"` → `done`

## Definition of Done

- [ ] 4 项门禁全部 PASS → FSM 推进到 Phase 1
- [ ] 任一门禁 FAIL → 返回具体原因，不推进
- [ ] 首次推进 → PreferenceExtractor → Modal → 确认 → 写入 → 推进
- [ ] 再次推进 → 跳过偏好提取 → 直接 GateKeeper → 推进
- [ ] nothing_found → 用户跳过 → preferences_confirmed_at 写入 → 推进
- [ ] Parent journey SPEC-J-003 playwright test 通过
