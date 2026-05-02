# SPEC-M-002: RequirementsAgent + requirements.json Schema

## Metadata

```yaml
spec_id: SPEC-M-002
delivery_kind: module
parent_journey: SPEC-J-001
evidence_type: eval_based
status: PENDING
allowed_files:
  - "src/backend/agents/requirements_agent.py"
  - "src/shared/schemas/requirements.py"
  - "config/platforms.json"
  - "config/categories.json"
  - "config/model_config.json"
forbidden_files: ["HARNESS.md", "CLAUDE.md", ".claude/**"]
```

## Why This Module Exists

RequirementsAgent 是 Phase 0 的核心生产者（Producer）：将用户的自然语言描述转化为结构化 `requirements.json`。它不从 LLM 推断技术参数（platform.specs 查表填入），仅从用户描述中提取语义信息（主题、观点、时长范围、平台偏好）。缺失关键维度时通过 `clarification_needed` 字段标记，而非编造细节。

## Consumer / Evidence

### evidence_type: eval_based

| Field | Value |
|---|---|
| Eval set path | `tests/eval/requirements_agent/` |
| Threshold | `accuracy ≥ 0.80, regression vs baseline ≤ 5%` |
| Verification command | `pytest tests/eval/requirements_agent/ --eval-mode -v` |
| Baseline file | `tests/eval/requirements_agent/baseline.json` |

## Interfaces

| name | params | returns | raises | example |
|---|---|---|---|---|
| `RequirementsAgent.generate(title, description)` | `title: str, description: str` | `RequirementsOutput` (Pydantic model) | `ValidationError` (Instructor 校验失败) | — |
| `RequirementsAgent.revise(current_json, user_feedback)` | `current: RequirementsOutput, feedback: str` | `RequirementsOutput` (合并更新) | `ValidationError` | — |

## Data Constraints

| target | rules |
|---|---|
| `requirements.json` | 必填字段：project_id, title, topic(≥5字符), user_input_content(含至少1个可识别观点) |
| `target_duration_minutes` | min ≥ 0, max ≥ min；min/max 可同为 null（用户未提供时长） |
| `target_word_count` | 公式：min = duration.min × 240 × 0.8, max = duration.max × 240 × 1.2；duration 为 null 时 word_count 也为 null |
| `platform.primary` | 必须在 `config/platforms.json` 中存在；未指定时默认 `bilibili` |
| `platform.specs` | 不从 LLM 推断，从 `config/platforms.json` 按 primary 查表填入 |
| `category` | level1/level2 必须在 `config/categories.json` 中存在 |
| `clarification_needed` | 值仅限：`specific_angle`/`duration`/`platform`/`category` |

## Exception Handling

| scenario | trigger | expected |
|---|---|---|
| LLM 返回非结构化输出 | Instructor 解析失败 | 自动重试（max 3 次，指数退避）；3 次后返回 `failed` |
| 用户描述极短（如"做个视频"） | 无法提取 topic ≥ 5 字符 | 不编造，clarification_needed 标记 multiple 维度，Agent 回复卡片列出所有澄清问题 |
| 平台不在配置中 | LLM 返回未知平台名 | Instructor 校验拦截（Pydantic validator 查 platforms.json），要求 LLM 重新输出 |

## Verification Commands

- `pytest tests/eval/requirements_agent/test_requirements_generation.py --eval-mode -v`
- `python scripts/assert_artifact.py --check "requirements.json" --rules "topic:min_length=5,platform:in_config"`
- `python -c "import json; d=json.load(open('data/projects/test/phase_0/requirements.json')); assert d['platform']['specs']['resolution']=='1920x1080'"` (验证 specs 来自配置文件而非 LLM 推断)

## Definition of Done

- [ ] Eval set accuracy ≥ 0.80，regression ≤ 5%
- [ ] `requirements.json` 所有字段约束通过 Pydantic 校验
- [ ] 澄清问题在 clarification_needed 非空时正确生成
- [ ] platform.specs 100% 来自 config/platforms.json 查表（eval 验证）
- [ ] Parent journey SPEC-J-001 的 playwright test 通过
