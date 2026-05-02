# [SPEC-P0-M4] 意图路由与需求修订（IntentRouter + Revision Pipeline）

## Metadata
- **task_id**: SPEC-P0-M4
- **spec_ref**: Phase0需求.md §5; TECH_PLAN_v3.3.md §3.1, §6, §8
- **depends_on**: [SPEC-P0-M2, SPEC-P0-M3]
- **priority**: P0
- **estimated_complexity**: L

## Scope
实现 IntentRouter 意图识别模块和需求修订流水线。Router 接收用户自然语言消息，识别为 revise / regenerate / inject_subtask / request_advance / clarify 五种动作。revise 和 regenerate 触发 RequirementsAgent 重新生成，artifact_version 自增，旧 review superseded，新 review 自动创建。clarify 不改动 task_ledger。

**业务闭环**: 用户自然语言反馈 → Router 识别意图 → 执行修订动作 → 产物更新 + 旧审核作废 + 新审核自动触发。

## Allowed Files
- `src/backend/engine/router.py`
- `src/backend/agents/requirements_agent.py`
- `src/backend/services/task_service.py`
- `src/backend/services/artifact_service.py`
- `tests/unit/engine/test_router.py`
- `tests/unit/agents/test_requirements_agent_revision.py`
- `tests/integration/test_revision_pipeline.py`

## Forbidden Files
- `src/frontend/**`
- `src/backend/api/**`
- `docs/specs/**`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: IntentRouter 接收用户消息 + 上下文（§6 注入规则），调用 LiteLLM（模型路由 `intent_router_primary: claude-haiku-4-5`，3s 超时），输出动作类型枚举
- [ ] AC-2: Router 识别 revise：用户消息含"改成""补充""应该是""从X角度"等修改意图关键词 → 输出 `revise`
- [ ] AC-3: Router 识别 regenerate：用户消息含"重做""重新来""不满意""换个方向"等 → 输出 `regenerate`
- [ ] AC-4: Router 识别 inject_subtask：用户消息含"帮我查""搜一下""调研"等 → 输出 `inject_subtask`
- [ ] AC-5: Router 识别 request_advance：用户消息含"下一步""继续""好了""没问题""确认"等 → 输出 `request_advance`
- [ ] AC-6: Router 识别 clarify：语义模糊置信度 < 0.6 或 JSON 解析失败/超时 → 输出 `clarify`；连续 2 次 clarify 后返回 4 个候选动作
- [ ] AC-7: revise 流程：追加 `user_revision` task → RequirementsAgent 以原 JSON + 用户消息为输入重新生成（二次关键信息提取：合并缺失维度、更新指定字段、保留未提及字段）→ artifact_version++ → 旧 review → superseded → 自动追加新 review
- [ ] AC-8: regenerate 流程：追加新 `generate_artifact` task → 从零重新生成 → artifact_version++ → 旧 review → superseded → 新 review 自动创建
- [ ] AC-9: 产物多版本管理：`requirements_v1.json`, `requirements_v2.json` 等；artifact_ref 指向最新版本
- [ ] AC-10: user_revision 只修改用户明确提到的字段，未提及字段保持不变
- [ ] AC-11: 依赖字段联动更新：如用户修改时长 → target_word_count 自动重算
- [ ] AC-12: request_advance 不自动推进，Router 返回引导文案

## Verification Commands
```bash
# Router unit tests - intent classification
pytest tests/unit/engine/test_router.py::test_router_classifies_revise -v
pytest tests/unit/engine/test_router.py::test_router_classifies_regenerate -v
pytest tests/unit/engine/test_router.py::test_router_classifies_inject_subtask -v
pytest tests/unit/engine/test_router.py::test_router_classifies_request_advance -v
pytest tests/unit/engine/test_router.py::test_router_classifies_clarify -v
pytest tests/unit/engine/test_router.py::test_router_fallback_on_timeout -v
pytest tests/unit/engine/test_router.py::test_router_double_clarify_returns_candidates -v

# RequirementsAgent revision tests
pytest tests/unit/agents/test_requirements_agent_revision.py::test_revise_updates_only_specified_fields -v
pytest tests/unit/agents/test_requirements_agent_revision.py::test_revise_recalculates_word_count -v
pytest tests/unit/agents/test_requirements_agent_revision.py::test_regenerate_from_scratch -v

# Integration tests - full revision pipeline
pytest tests/integration/test_revision_pipeline.py::test_revise_flow_supersedes_old_review -v
pytest tests/integration/test_revision_pipeline.py::test_regenerate_flow_creates_new_artifact -v
pytest tests/integration/test_revision_pipeline.py::test_artifact_version_increments -v

# Type check
mypy src/backend/engine/router.py --strict
```

## Completion Definition
IntentRouter 正确识别 5 种动作类型，超时/解析失败回退为 clarify。revise 和 regenerate 流程完整：产物版本管理正确、旧 review superseded、新 review 自动创建。字段联动更新正确。全部测试通过。

## Test Mapping
| AC | 手动测试场景 | 检查点 |
|---|---|---|
| AC-2, AC-7, AC-10 | 场景 2.1 — revise 时长 | 2.1b user_revision 任务 running |
| AC-2, AC-7, AC-10 | 场景 2.1 — 字段更新 | 2.1d duration 变为 15min |
| AC-2, AC-7, AC-11 | 场景 2.1 — 字数重算 | 2.1d word_count 重算 |
| AC-2, AC-7 | 场景 2.1 — review 作废 | 2.1e 旧 review superseded |
| AC-2, AC-7 | 场景 2.1 — 新 review | 2.1f 新 review 任务 |
| AC-2, AC-7 | 场景 2.2 — revise 平台 | 2.2a primary 变为 wechat |
| AC-2, AC-7 | 场景 2.2 — specs 更新 | 2.2b 1080x1920/4Mbps |
| AC-2, AC-7 | 场景 2.2 — secondary 不含旧值 | 2.2c 不含 bilibili |
| AC-2, AC-7 | 场景 2.2 — 版本自增 | 2.2d v2→v3 |
| AC-3, AC-8 | 场景 2.3 — regenerate | 2.3a 新 generate_artifact 任务 |
| AC-3, AC-8 | 场景 2.3 — 新卡片 | 2.3c 全新需求摘要卡片 |
| AC-6 | 场景 2.4 — clarify | 2.4a 澄清回复 |
| AC-6 | 场景 2.4 — 不改账本 | 2.4b 无新任务 |
| AC-7 | 场景 3.2 — 澄清补充 | 3.2a 字段更新 |
