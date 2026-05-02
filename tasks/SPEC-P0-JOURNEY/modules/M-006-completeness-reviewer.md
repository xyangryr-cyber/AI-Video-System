# SPEC-M-006: CompletenessReviewer

## Metadata

```yaml
spec_id: SPEC-M-006
delivery_kind: module
parent_journey: SPEC-J-002
evidence_type: eval_based
status: PENDING
allowed_files:
  - "src/backend/agents/completeness_reviewer.py"
  - "src/shared/schemas/review.py"
forbidden_files: ["HARNESS.md", "CLAUDE.md", ".claude/**"]
```

## Why This Module Exists

CompletenessReviewer 对 RequirementsAgent 的输出做二元判定（PASS/FAIL）。8 项检查覆盖主题/内容/时长/字数/平台/规格/分类/澄清标记。每次 revise/regenerate 后自动触发新 review（旧 review → superseded），确保每次修改都经过质量门禁。审核结果对用户透明（PASS → 可推进，FAIL → 明确告知缺失维度）。

## Consumer / Evidence

### evidence_type: eval_based

| Field | Value |
|---|---|
| Eval set path | `tests/eval/completeness_reviewer/` |
| Threshold | `accuracy ≥ 0.85, regression vs baseline ≤ 5%` |
| Verification command | `pytest tests/eval/completeness_reviewer/ --eval-mode -v` |
| Baseline file | `tests/eval/completeness_reviewer/baseline.json` |

## Interfaces

| name | params | returns | raises | example |
|---|---|---|---|---|
| `CompletenessReviewer.review(requirements_json)` | `requirements: RequirementsOutput` | `ReviewResult {verdict: PASS\|FAIL, notes: str[], blocking_issues: str[]}` | `ValidationError` | — |

## Data Constraints

| target | rules |
|---|---|
| verdict | `PASS` 或 `FAIL`（二元） |
| blocking_issues | 仅列出导致 FAIL 的项；PASS 时为空数组 |
| 8 项检查 | 主题(≥5字)/内容(含观点)/时长(min≥0,max≥min)/字数(一致性)/平台(在config中存在)/规格(与config一致)/分类(在config中存在)/澄清标记(值在已知列表中) |

## Exception Handling

| scenario | trigger | expected |
|---|---|---|
| Reviewer LLM 调用失败 | API 超时/报错 | 自动重试（max 3 次）；3 次后 task status = `failed`，前端显示"审核服务异常，请稍后重试" |
| requirements.json 格式损坏 | JSON 解析失败 | 直接返回 FAIL，blocking_issues = ["产物文件格式异常"] |
| 平台 specs 与 config 不一致 | LLM 修改了 specs 字段 | FAIL + "视频规格与平台配置不一致"（这是 revise 引入的典型 bug） |

## Verification Commands

- `pytest tests/eval/completeness_reviewer/test_reviewer_accuracy.py --eval-mode -v`
- `pytest tests/unit/backend/agents/test_completeness_reviewer.py -v`
- `python scripts/assert_artifact.py --check "review_result.json" --rules "verdict:in={PASS,FAIL}"`

## Definition of Done

- [ ] Eval set accuracy ≥ 0.85
- [ ] 8 项检查全部有 PASS case + FAIL case 覆盖
- [ ] FAIL 时 blocking_issues 非空且原因明确
- [ ] 平台 specs 不一致时正确检出（不遗漏）
- [ ] Parent journey SPEC-J-002 playwright test 通过
