# [SPEC-P0-M2] 需求生成 Agent（RequirementsAgent）

## Metadata
- **task_id**: SPEC-P0-M2
- **spec_ref**: Phase0需求.md §3; TECH_PLAN_v3.3.md §1, §3.4, §6
- **depends_on**: [SPEC-P0-M1]
- **priority**: P0
- **estimated_complexity**: M

## Scope
实现 RequirementsAgent 无状态函数，将用户自然语言描述转化为结构化 `requirements.json`。包含 LLM 调用（LiteLLM + Instructor）、配置文件查表补全、澄清逻辑、字数计算、`agent_call_log` 写入。同时实现 `generate_artifact` task 的生命周期管理。

**业务闭环**: 用户自然语言描述 → LLM 提取语义 + 查表补全技术参数 → 结构化 `requirements.json`（含澄清标记）。

## Allowed Files
- `src/backend/agents/requirements_agent.py`
- `src/backend/services/llm_service.py`
- `src/shared/schemas/requirements_schema.py`
- `tests/unit/agents/test_requirements_agent.py`
- `tests/fixtures/requirements_fixtures.py`

## Forbidden Files
- `src/frontend/**`
- `src/backend/engine/**`
- `src/backend/api/**`
- `docs/specs/**`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: RequirementsAgent 接收 title + description，调用 LiteLLM（模型路由 `requirements_agent: openai/deepseek-v4-pro`），通过 Instructor 校验输出 schema
- [ ] AC-2: 输出 `requirements.json` 包含全部必填字段：project_id / title / topic（≥5字符）/ user_input_content / target_duration_minutes / target_word_count / platform（primary + secondary + specs）/ category（level1 + level2）/ clarification_needed / created_at
- [ ] AC-3: platform.specs 从 `config/platforms.json` 按 primary 查表填入，不由 LLM 推断
- [ ] AC-4: category.level1 和 level2 从 `config/categories.json` 中匹配，值必须在配置中存在
- [ ] AC-5: target_word_count 按公式计算：min = duration.min × speech_rate × 0.8, max = duration.max × speech_rate × 1.2；speech_rate 从 `config/model_config.json` 读取（默认 240）
- [ ] AC-6: 用户未提供时长时，target_duration_minutes 为 {min: null, max: null}，target_word_count 为 null，clarification_needed 包含 "duration"
- [ ] AC-7: 用户未提供平台时，platform.primary 取默认值 "bilibili"（从 `config/platforms.json` 的 default_platform 读取），secondary 为空数组
- [ ] AC-8: 缺失关键维度时 clarification_needed 数组标记对应 key（specific_angle / duration / platform / category），不阻塞 JSON 生成
- [ ] AC-9: 信息完整时 clarification_needed 为空数组
- [ ] AC-10: 每次调用写入 agent_call_log（agent_name / model / tokens_input / tokens_output / duration_ms / cost_usd）
- [ ] AC-11: generate_artifact task 状态正确流转：pending → queued → running → succeeded（或 failed）

## Verification Commands
```bash
# Unit tests - valid input produces all fields
pytest tests/unit/agents/test_requirements_agent.py::test_full_input_generates_all_fields -v

# Unit tests - specs from config, not LLM inference
pytest tests/unit/agents/test_requirements_agent.py::test_platform_specs_from_config -v

# Unit tests - word count calculation
pytest tests/unit/agents/test_requirements_agent.py::test_word_count_calculation -v

# Unit tests - incomplete input triggers clarification
pytest tests/unit/agents/test_requirements_agent.py::test_missing_duration_triggers_clarification -v

# Unit tests - category matching
pytest tests/unit/agents/test_requirements_agent.py::test_category_matches_config_enum -v

# Unit tests - agent call log
pytest tests/unit/agents/test_requirements_agent.py::test_agent_call_log_written -v

# Type check
mypy src/backend/agents/requirements_agent.py --strict
```

## Completion Definition
RequirementsAgent 可从完整输入生成含全部字段的 requirements.json，从残缺输入生成含 clarification_needed 标记的 JSON。specs/category 100% 从配置文件查表，不由 LLM 推断。字数计算正确。agent_call_log 每次写入。全部测试通过。

## Test Mapping
| AC | 手动测试场景 | 检查点 |
|---|---|---|
| AC-2, AC-3, AC-5 | 场景 1.3 — 需求生成 | 1.3a 需求摘要卡片含标题/主题/时长/平台/分类 |
| AC-3 | 场景 1.3 — 平台规格 | 1.3b B站参数 1920x1080/8Mbps/H.264 |
| AC-5 | 场景 1.3 — 字数计算 | 1.3c 1536~2880 字 |
| AC-8 | 场景 3.1 — 不完整描述 | 3.1a 澄清问题区域 |
| AC-8 | 场景 3.1 — 澄清标记 | 3.1b specific_angle/duration/platform |
| AC-8 | 场景 3.1 — 不编造 | 3.1c 无编造细节 |
| AC-9 | 场景 3.1 — 合法字段 | 3.1d 已推断字段绿色勾 |
