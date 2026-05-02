# [SPEC-C-009] Producer Agent Template, Streaming & Decision Rationale

## Metadata
- **task_id**: SPEC-C-009
- **spec_ref**: SPEC-5.1, SPEC-5.7, SPEC-5.9
- **depends_on**: [SPEC-A-001, SPEC-C-001, SPEC-C-011]
- **priority**: P0
- **estimated_complexity**: L

## Scope
Implement the Producer Agent with: (1) a system prompt template containing exactly 7 mandatory fields (`role_name`, `task_description`, `input_artifacts`, `output_schema`, `user_preferences`, `quality_criteria`, `prohibitions`) -- missing any field raises an exception; (2) WebSocket streaming output for artifact generation (TTFT <3s, token concatenation equals final artifact); (3) mandatory `decision_rationale` field (>=20 chars) in every Producer output schema, validated by Instructor.

## Allowed Files
- `src/backend/agents/producer_agent.py`
- `src/backend/agents/prompt_templates.py`
- `src/backend/agents/__init__.py`
- `tests/unit/backend-core/test_producer_agent.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**` (owned by SPEC-A)
- `src/backend/api/**`

## Acceptance Criteria
- [ ] AC-1: Prompt template contains exactly 7 mandatory field placeholders
- [ ] AC-2: Rendering with any missing mandatory field raises an exception
- [ ] AC-3: TTFT (first token arrival) < 3 seconds
- [ ] AC-4: Concatenating all streamed tokens after `done` event equals the final artifact
- [ ] AC-5: `decision_rationale` field is required in output schema, length >= 20 chars
- [ ] AC-6: Missing `decision_rationale` triggers Instructor retry

## Verification Commands
```bash
pytest tests/unit/backend-core/test_spec_c_009.py -v
ruff check src/backend/agents/producer_agent.py src/backend/agents/prompt_templates.py
mypy src/backend/agents/producer_agent.py --strict
```

## Completion Definition
Producer Agent renders prompts from the 7-field template, streams output via WebSocket, and enforces decision_rationale. All validation and streaming tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/backend-core/test_spec_c_009.py | test_template_has_seven_fields |
| AC-2 | tests/unit/backend-core/test_spec_c_009.py | test_missing_field_raises |
| AC-3 | tests/unit/backend-core/test_spec_c_009.py | test_ttft_under_3s |
| AC-4 | tests/unit/backend-core/test_spec_c_009.py | test_streamed_tokens_equal_final |
| AC-5 | tests/unit/backend-core/test_spec_c_009.py | test_decision_rationale_required |
| AC-6 | tests/unit/backend-core/test_spec_c_009.py | test_missing_rationale_retries |
