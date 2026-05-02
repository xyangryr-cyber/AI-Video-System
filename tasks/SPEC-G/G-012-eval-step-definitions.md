# [SPEC-G-012] Eval BDD Step Definitions 补齐

## Metadata
- **task_id**: SPEC-G-012
- **spec_ref**: SPEC-G5.1
- **depends_on**: []
- **priority**: P1
- **estimated_complexity**: M
- **TDD 起点**: 6 个 eval BDD scenario 当前 FAIL（视为 RED，因 step definitions 缺失）→ 补齐 step implementations → PASS（GREEN）

## Scope
为 `tests/eval/bdd/` 的 6 个失败场景补齐缺失的 step definitions。所有 6 个场景失败原因相同: feature 文件中的 Given/When/Then 措辞在 `tests/eval/bdd/steps/` 中没有对应实现。Eval bucket 由 `AVS_EVAL_MODE=1` 控制，不在日常 CI loop 中。

## Allowed Files
- `tests/eval/bdd/steps/classification_steps.py`

## Forbidden Files
- `src/backend/**` (IntentRouter 实现正确，不修改)
- `src/frontend/**`
- `docs/specs/**`

## Acceptance Criteria
- [ ] AC-1: "用户要求整体重做时识别为 regenerate" → PASS (Given "当前阶段已有已生成主产物")
- [ ] AC-2: "用户要求补充调研时识别为 inject_subtask" → PASS (Given "当前阶段允许插入 research 或 verify 子任务")
- [ ] AC-3: "用户表达下一步意图时不直接推进而是引导 confirm_next" → PASS (Given "当前阶段的推进入口是硬按钮 confirm_next")
- [ ] AC-4: "无法识别的输入进入 clarify" → PASS (When "IntentRouter 无法从上下文中识别具体意图")
- [ ] AC-5: "连续两轮 clarify 后展示候选动作" → PASS (Given "同一条会话连续两轮 Router 输出 action=clarify")
- [ ] AC-6: "跨阶段不继承无关对话历史" → PASS (Given "当前已从 Phase 2 进入 Phase 3")

## Verification Commands
```bash
AVS_EVAL_MODE=1 pytest tests/eval/bdd/ -v
ruff check tests/eval/bdd/steps/classification_steps.py
.venv/bin/python3 scripts/contracts/verify_no_skip_stubs.py
```

## Completion Definition
`AVS_EVAL_MODE=1 pytest tests/eval/bdd/ -v` 6/7 passed (1 个已在 baseline 中 skip)。完成后追加一行 commit 到 `PROGRESS.md`。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1..6 | tests/eval/bdd/test_classification_bdd.py | 6 router scenarios |
