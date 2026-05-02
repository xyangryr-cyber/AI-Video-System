# [SPEC-P0-M3] 完整性审核 Agent（CompletenessReviewer）

## Metadata
- **task_id**: SPEC-P0-M3
- **spec_ref**: Phase0需求.md §4; TECH_PLAN_v3.3.md §1, §6
- **depends_on**: [SPEC-P0-M2]
- **priority**: P0
- **estimated_complexity**: M

## Scope
实现 CompletenessReviewer 无状态函数，对 RequirementsAgent 输出的 `requirements.json` 执行 8 项审核清单，输出 PASS/FAIL 二元判定。实现 review task 自动触发机制和生命周期管理。FAIL 时不阻塞账本，但前端显示 blocking_issues。

**业务闭环**: `requirements.json` 生成完成 → 自动触发审核 → PASS（可推进）或 FAIL（列出阻塞项供用户修改）。

## Allowed Files
- `src/backend/agents/reviewers/completeness_reviewer.py`
- `src/backend/services/llm_service.py`
- `tests/unit/agents/test_completeness_reviewer.py`
- `tests/fixtures/review_fixtures.py`

## Forbidden Files
- `src/frontend/**`
- `src/backend/api/**`
- `docs/specs/**`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: CompletenessReviewer 接收 requirements.json，调用 LiteLLM（模型路由 `reviewer: claude-sonnet`），输出 `{verdict, notes[], blocking_issues[]}`
- [ ] AC-2: 审核项 1 — 主题非空且长度 ≥ 5 字符；空或模糊 → FAIL
- [ ] AC-3: 审核项 2 — user_input_content 非空且含至少一个可识别观点；空 → FAIL
- [ ] AC-4: 审核项 3 — target_duration_minutes 非 null 时 min ≥ 0 且 max ≥ min；违反 → FAIL
- [ ] AC-5: 审核项 4 — 字数一致性：duration 非 null 时 word_count min > 0 且 max > min；duration 为 null 时 word_count 也为 null；不一致 → FAIL
- [ ] AC-6: 审核项 5 — platform.primary 在 config/platforms.json 中存在；不存在 → FAIL
- [ ] AC-7: 审核项 6 — specs（resolution/bitrate/format）均非空且与 config/platforms.json 定义一致；不符 → FAIL
- [ ] AC-8: 审核项 7 — category.level1 和 level2 均非空且在 config/categories.json 中存在；无效 → FAIL
- [ ] AC-9: 审核项 8 — clarification_needed 数组存在，每个值在已知维度列表（duration/specific_angle/platform/category）中；未知值 → FAIL
- [ ] AC-10: generate_artifact  succeeded 后自动创建 review task（depends_on: generate_artifact），状态 pending → queued → running → succeeded/failed
- [ ] AC-11: review FAIL 时不阻塞 task_ledger（账本正常记录），但 blocking_issues 数组非空
- [ ] AC-12: 每次调用写入 agent_call_log

## Verification Commands
```bash
# Unit tests - all 8 review items
pytest tests/unit/agents/test_completeness_reviewer.py::test_pass_on_complete_requirements -v
pytest tests/unit/agents/test_completeness_reviewer.py::test_fail_on_empty_topic -v
pytest tests/unit/agents/test_completeness_reviewer.py::test_fail_on_no_user_content -v
pytest tests/unit/agents/test_completeness_reviewer.py::test_fail_on_invalid_duration -v
pytest tests/unit/agents/test_completeness_reviewer.py::test_fail_on_word_count_inconsistency -v
pytest tests/unit/agents/test_completeness_reviewer.py::test_fail_on_unknown_platform -v
pytest tests/unit/agents/test_completeness_reviewer.py::test_fail_on_specs_mismatch -v
pytest tests/unit/agents/test_completeness_reviewer.py::test_fail_on_invalid_category -v
pytest tests/unit/agents/test_completeness_reviewer.py::test_fail_on_unknown_clarification_key -v

# Unit tests - auto-trigger and lifecycle
pytest tests/unit/agents/test_completeness_reviewer.py::test_auto_create_review_task -v
pytest tests/unit/agents/test_completeness_reviewer.py::test_review_task_lifecycle -v

# Unit tests - agent call log
pytest tests/unit/agents/test_completeness_reviewer.py::test_agent_call_log_written -v

# Type check
mypy src/backend/agents/reviewers/completeness_reviewer.py --strict
```

## Completion Definition
CompletenessReviewer 正确执行全部 8 项审核，PASS/FAIL 判定准确。review task 在 generate_artifact 成功后自动创建并正确流转。FAIL 时不阻塞账本。agent_call_log 每次写入。全部测试通过。

## Test Mapping
| AC | 手动测试场景 | 检查点 |
|---|---|---|
| AC-1, AC-10 | 场景 1.4 — 审核通过 | 1.4a review → ✅ succeeded |
| AC-1, AC-10 | 场景 1.4 — 按钮可用 | 1.4b-c 确认按钮高亮可点击 |
| AC-11 | 场景 3.1 — 不完整信息审核 | 3.1a-e 审核 FAIL 但卡片渲染澄清问题 |
| AC-11 | 场景 3.3 — 补充后审核通过 | 3.3a review PASS |
| AC-11 | 场景 3.3 — 澄清清空 | 3.3b clarification_needed 为空 |
