# SPEC-M-009: PreferenceExtractor

## Metadata

```yaml
spec_id: SPEC-M-009
delivery_kind: module
parent_journey: SPEC-J-003
evidence_type: eval_based
status: PENDING
allowed_files:
  - "src/backend/agents/preference_extractor.py"
  - "src/shared/schemas/preferences.py"
forbidden_files: ["HARNESS.md", "CLAUDE.md", ".claude/**"]
```

## Why This Module Exists

PreferenceExtractor 在用户首次点击"确认进入下一阶段"时被 API 层同步调用（不在 task_ledger 中）。它从 Phase 0 对话历史中提取用户的隐式偏好规则（如"用户倾向 8-12 分钟中等偏长视频""用户倾向从技术角度分析"），输出候选偏好列表供用户确认。每条候选偏好必须包含 evidence（不能为空）且 confidence ≥ 0.6。与已有偏好冲突的必须在 `conflicts_with` 列出。

## Consumer / Evidence

### evidence_type: eval_based

| Field | Value |
|---|---|
| Eval set path | `tests/eval/preference_extractor/` |
| Threshold | `precision ≥ 0.75, recall ≥ 0.70, regression ≤ 5%` |
| Verification command | `pytest tests/eval/preference_extractor/ --eval-mode -v` |
| Baseline file | `tests/eval/preference_extractor/baseline.json` |

## Interfaces

| name | params | returns | raises | example |
|---|---|---|---|---|
| `PreferenceExtractor.extract(dialogue_history, revision_instructions, artifact_diff, existing_preferences)` | `dialogue: str, revisions: str[], diff: str, existing: Preference[]` | `PreferenceResult {candidates: Candidate[], nothing_found: bool}` | — | — |

## Data Constraints

| target | rules |
|---|---|
| Candidate.rule | 非空；自然语言描述偏好规则 |
| Candidate.evidence | 非空；引用对话片段作为依据 |
| Candidate.confidence | 0.6 ~ 1.0；< 0.6 不进入 candidates |
| Candidate.conflicts_with | 与已有偏好冲突时列出冲突项；无冲突为 null |
| Candidate.scope_suggestion | `project` 或 `global` |
| nothing_found | true 时 candidates 为空数组，前端显示"未发现新偏好"，用户需点击"跳过" |

## Exception Handling

| scenario | trigger | expected |
|---|---|---|
| 无对话历史 | 用户直接提交后立即点推进（无交互） | nothing_found = true，不报错 |
| LLM 返回 confidence < 0.6 的候选 | Instructor 输出低置信度 | 过滤掉，不进入 candidates |
| evidence 字段为空 | LLM 输出缺少 evidence | Instructor 校验拦截，要求重新输出（max 3 次） |

## Verification Commands

- `pytest tests/eval/preference_extractor/test_extractor_accuracy.py --eval-mode -v`
- `pytest tests/unit/backend/agents/test_preference_extractor.py -v`
- `python scripts/assert_artifact.py --check "preferences_candidates.json" --rules "evidence:non_empty,confidence:gte=0.6"`

## Definition of Done

- [ ] precision ≥ 0.75, recall ≥ 0.70
- [ ] evidence 非空 + confidence ≥ 0.6 硬约束通过 eval 验证
- [ ] nothing_found = true 时正确处理
- [ ] 与已有偏好冲突时正确标记 conflicts_with
- [ ] Parent journey SPEC-J-003 playwright test 通过
