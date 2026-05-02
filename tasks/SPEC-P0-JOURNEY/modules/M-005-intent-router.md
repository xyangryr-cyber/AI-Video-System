# SPEC-M-005: Intent Router

## Metadata

```yaml
spec_id: SPEC-M-005
delivery_kind: module
parent_journey: SPEC-J-002
evidence_type: eval_based
status: PENDING
allowed_files:
  - "src/backend/engine/router.py"
  - "config/model_config.json"
forbidden_files: ["HARNESS.md", "CLAUDE.md", ".claude/**"]
```

## Why This Module Exists

Router 是用户自然语言对话交互的"中枢神经系统"。用户在对话区输入的消息可能是修改需求（revise）、重做（regenerate）、调研请求（inject_subtask）、推进请求（request_advance），也可能是模糊意图。Router 负责以最小成本（轻量 LLM 或规则匹配）识别意图并输出动作枚举值，不执行任何操作。Router 误判 = 用户意图被错误路由，直接影响体验。

## Consumer / Evidence

### evidence_type: eval_based

| Field | Value |
|---|---|
| Eval set path | `tests/eval/intent_router/` |
| Threshold | `accuracy ≥ 0.85, regression vs baseline ≤ 5%` |
| Verification command | `pytest tests/eval/intent_router/ --eval-mode -v` |
| Baseline file | `tests/eval/intent_router/baseline.json` |

## Interfaces

| name | params | returns | raises | example |
|---|---|---|---|---|
| `Router.classify(message, context)` | `message: str, context: RouterContext` | `RouterResult {action: ActionEnum, confidence: float}` | — | `"改成15分钟"` → `{action: revise, confidence: 0.92}` |

## Data Constraints

| target | rules |
|---|---|
| ActionEnum | `revise` / `regenerate` / `inject_subtask` / `request_advance` / `clarify` |
| confidence | 0.0 ~ 1.0；< 0.6 → action = `clarify` |
| Router 模型 | `intent_router_primary: "claude-haiku-4-5"`（低成本模型，不消耗生产模型 token） |

## Exception Handling

| scenario | trigger | expected |
|---|---|---|
| 模糊意图 | confidence < 0.6 | 返回 `clarify`，前端显示追问（如"你是想修改需求，还是进入下一阶段？"），不改动账本 |
| LLM 调用失败 | Router 模型 API 超时/报错 | 降级为规则匹配（关键词正则）；规则也无法匹配时返回 `clarify` |
| 空消息 | message.trim() === "" | 返回 `clarify`，不调用 LLM |

## Verification Commands

- `pytest tests/eval/intent_router/test_router_accuracy.py --eval-mode -v`
- `pytest tests/unit/backend/engine/test_router.py -v`
- `python -c "from backend.engine.router import Router; r=Router.classify('改成15分钟', {}); assert r.action=='revise'"`

## Definition of Done

- [ ] Eval set accuracy ≥ 0.85
- [ ] 5 种 action 全部有 eval case 覆盖
- [ ] confidence < 0.6 时正确返回 clarify
- [ ] LLM 不可用时降级为规则匹配（不崩溃）
- [ ] Parent journey SPEC-J-002 playwright test 通过
