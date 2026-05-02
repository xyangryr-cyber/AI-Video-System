# [SPEC-C-100] SafetyGuard / SafetyPolicyEngine 子系统

## Metadata
- **task_id**: SPEC-C-100
- **spec_ref**: `SPEC-C` §C-BDD-1(重编号 SPEC-4.5-Clarify 见风险 R-1)
- **depends_on**: []
- **priority**: P0
- **estimated_complexity**: L
- **bdd_tags**: [@safety]

## Scope
实现 SafetyGuard / SafetyPolicyEngine 输入安全子系统：输入分类、5 档策略决策（allow/clarify/restrict/refuse/转人工）、模板化响应生成、热更新配置与命中事件埋点。⚠️ 风险 R-1：本任务需对齐 v3.15 已有 SPEC-4.5 的代码引用，避免与旧版安全策略实现冲突。

## Allowed Files
- `src/backend/agents/safety_policy_engine.py`
- `src/backend/agents/safety/input_classifier.py`
- `src/backend/agents/safety/policy_decision.py`
- `src/backend/agents/safety/response_generator.py`
- `config/safety_input_rules.yaml`
- `config/safety_templates.yaml`
- `tests/unit/agents/test_safety_policy_engine.py`
- `tests/eval/safety_eval_set.jsonl`

## Acceptance Criteria
- [ ] AC-1: 5 档决策 allow/clarify/restrict/refuse/转人工 全覆盖
- [ ] AC-2: refuse/restrict 不调 LLM(纯模板返回)
- [ ] AC-3: 误杀率 < 5% 漏放率 < 1%(eval 集度量)
- [ ] AC-4: 命中写 `events.event_type=safety.blocked`,含 user_input_hash,不存原文
- [ ] AC-5: 配置热更新:`config/safety_templates.yaml` 改动后 60s 内生效

## Verification Commands
```bash
pytest tests/unit/backend-core/test_spec_c_100.py -v
```

## Completion Definition
SafetyPolicyEngine 5 档决策全覆盖且 refuse/restrict 路径零 LLM 调用，eval 集误杀率 < 5%、漏放率 < 1%，命中事件正确埋点（仅 hash），模板配置 60s 热更新生效，全部 AC 与单元/eval 测试通过。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/backend-core/test_spec_c_100.py | test_five_decision_levels_full_coverage |
| AC-2 | tests/unit/backend-core/test_spec_c_100.py | test_refuse_restrict_no_llm_call |
| AC-3 | tests/eval/safety_eval_set.jsonl | test_false_positive_under_5pct_false_negative_under_1pct |
| AC-4 | tests/unit/backend-core/test_spec_c_100.py | test_safety_blocked_event_emits_hash_only |
| AC-5 | tests/unit/backend-core/test_spec_c_100.py | test_safety_templates_hot_reload_within_60s |
