# [SPEC-P0-M5] 偏好提取与阶段门禁（PreferenceExtractor + GateKeeper）

## Metadata
- **task_id**: SPEC-P0-M5
- **spec_ref**: Phase0需求.md §6, §13; TECH_PLAN_v3.3.md §1, §3.3, §8
- **depends_on**: [SPEC-P0-M3, SPEC-P0-M4]
- **priority**: P0
- **estimated_complexity**: L

## Scope
实现 PreferenceExtractor（从对话历史中提取用户偏好候选）、偏好写入逻辑、GateKeeper 纯函数门禁校验、FSM 阶段推进。`POST /projects/{id}/advance` 首次调用触发偏好提取流程，完成后写入 `preferences_confirmed_at`。GateKeeper 执行 4 项程序化检查（零 LLM 成本），全部 PASS 后推进到 Phase 1。

**业务闭环**: 对话历史积累 → 提取偏好候选 → 用户确认 → 写入偏好库 → GateKeeper 校验 → Phase 0 完成，推进到 Phase 1。

## Allowed Files
- `src/backend/engine/preference_extractor.py`
- `src/backend/engine/gatekeeper.py`
- `src/backend/engine/fsm.py`
- `src/backend/services/preference_service.py`
- `src/backend/api/advance.py`
- `tests/unit/engine/test_preference_extractor.py`
- `tests/unit/engine/test_gatekeeper.py`
- `tests/unit/engine/test_fsm.py`
- `tests/integration/test_advance_flow.py`

## Forbidden Files
- `src/frontend/**`
- `src/backend/agents/requirements_agent.py`
- `docs/specs/**`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: PreferenceExtractor 以对话历史 + revision 指令 + 产物 diff + 已有偏好为输入，调用 LiteLLM（模型路由 `reviewer: claude-sonnet`），输出 candidates[]（每条含 rule / scope_suggestion / evidence / confidence / conflicts_with）
- [ ] AC-2: evidence 不能为空，confidence < 0.6 不进入 candidates，与已有偏好冲突必须在 conflicts_with 列出
- [ ] AC-3: nothing_found = true 时 candidates 为空数组，仍需用户显式跳过
- [ ] AC-4: `POST /projects/{id}/advance` 检查 preferences_confirmed_at 是否为 null：null → 返回 `{action: "confirm_preferences", candidates: [...]}`；非 null → 直接进入 GateKeeper
- [ ] AC-5: `POST /projects/{id}/preferences/confirm` 按 scope 写入：scope=project → project_preferences_md；scope=global → user_preferences_md；写入后 preferences_confirmed_at = now()
- [ ] AC-6: GateKeeper 为纯函数（不调 LLM），检查 4 项：① requirements.json 存在且 JSON Schema 校验通过 ② review verdict = PASS ③ task_ledger 所有 task 处于终态 ④ preferences_confirmed_at 非空
- [ ] AC-7: GateKeeper 全部 PASS → phase_0.status = "done" → FSM 推进到 Phase 1 → Phase 1 task_ledger 按 phase_templates.json 初始化
- [ ] AC-8: GateKeeper 任一 FAIL → 返回 `{status: "blocked", reasons: [...]}`，phase_0.status 不变
- [ ] AC-9: POST /projects/{id}/preferences/confirm 接收空 candidates（全部拒绝/nothing_found）→ 不写入偏好 → preferences_confirmed_at 仍写入 now()
- [ ] AC-10: 偏好写入后自动重新调用 GateKeeper → 通过则推进

## Verification Commands
```bash
# PreferenceExtractor unit tests
pytest tests/unit/engine/test_preference_extractor.py::test_extracts_preferences_from_dialogue -v
pytest tests/unit/engine/test_preference_extractor.py::test_filters_low_confidence -v
pytest tests/unit/engine/test_preference_extractor.py::test_detects_conflicts -v
pytest tests/unit/engine/test_preference_extractor.py::test_nothing_found_empty_candidates -v

# GateKeeper unit tests
pytest tests/unit/engine/test_gatekeeper.py::test_gate_all_pass -v
pytest tests/unit/engine/test_gatekeeper.py::test_gate_fail_missing_artifact -v
pytest tests/unit/engine/test_gatekeeper.py::test_gate_fail_review_not_pass -v
pytest tests/unit/engine/test_gatekeeper.py::test_gate_fail_tasks_not_terminal -v
pytest tests/unit/engine/test_gatekeeper.py::test_gate_fail_preferences_not_confirmed -v

# FSM unit tests
pytest tests/unit/engine/test_fsm.py::test_fsm_transition_p0_to_p1 -v
pytest tests/unit/engine/test_fsm.py::test_fsm_initializes_p1_task_ledger -v

# Integration tests
pytest tests/integration/test_advance_flow.py::test_first_advance_triggers_preferences -v
pytest tests/integration/test_advance_flow.py::test_confirm_preferences_then_advance -v
pytest tests/integration/test_advance_flow.py::test_empty_candidates_skip_flow -v

# Type check
mypy src/backend/engine/preference_extractor.py --strict
mypy src/backend/engine/gatekeeper.py --strict
mypy src/backend/engine/fsm.py --strict
```

## Completion Definition
PreferenceExtractor 从对话历史中正确提取偏好候选，硬约束（evidence/confidence/conflicts）全部执行。GateKeeper 纯函数 4 项检查无 LLM 调用。FSM 正确推进到 Phase 1 并初始化新阶段 task_ledger。偏好确认全流程（接受/拒绝/nothing_found）均可正确执行。全部测试通过。

## Test Mapping
| AC | 手动测试场景 | 检查点 |
|---|---|---|
| AC-1, AC-2 | 场景 4.2 — 偏好内容检查 | 4.2a 偏好含 rule/evidence/confidence |
| AC-1, AC-2 | 场景 4.2 — 偏好内容检查 | 4.2b evidence 非空 |
| AC-1 | 场景 4.2 — 偏好内容检查 | 4.2c 每条可选 project/global |
| AC-4 | 场景 4.1 — 触发偏好 | 4.1a 点击按钮触发偏好 |
| AC-4 | 场景 4.1 — 触发偏好 | 4.1b Modal 弹出 |
| AC-5, AC-7 | 场景 4.3 — 编辑+确认 | 4.3a 编辑偏好文字 |
| AC-5, AC-7 | 场景 4.3 — 编辑+确认 | 4.3b 保存并推进 |
| AC-5, AC-7 | 场景 4.4 — 门禁通过 | 4.4a Phase 0 绿色勾 |
| AC-5, AC-7 | 场景 4.4 — 门禁通过 | 4.4b Phase 1 高亮 |
| AC-5, AC-7 | 场景 4.4 — 门禁通过 | 4.4c 任务清单更新 |
| AC-6, AC-7 | 场景 5.1 — 跨项目复用 | 5.1a 新项目复用全局偏好 |
| AC-6, AC-7 | 场景 5.2 — 覆盖历史偏好 | 5.2a 新偏好覆盖旧偏好 |
