# [SPEC-C-011] LiteLLM + Instructor Integration & Model Routing Config

## Metadata
- **task_id**: SPEC-C-011
- **spec_ref**: SPEC-5.4, SPEC-5.5
- **depends_on**: [SPEC-A-001]
- **priority**: P0
- **estimated_complexity**: M

## Scope
Establish the unified LLM calling layer: all LLM calls go through LiteLLM (no direct `openai.ChatCompletion`), structured output via Instructor with Pydantic model binding and up to 3 retries on format errors. Configure model routing via `model_config.json` with 5 role keys: `intent_router_primary` (claude-haiku-4-5), `reviewer` (claude-sonnet), `gatekeeper` (claude-sonnet), `producer` (doubao-pro), `subtask` (doubao-pro). Config read via `GET /api/settings`, write via `PUT /api/settings/model-config`.

## Allowed Files
- `src/backend/services/llm_service.py`
- `src/backend/services/__init__.py`
- `config/model_config.json`
- `tests/unit/backend-core/test_llm_service.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: No direct `openai.ChatCompletion` calls anywhere in `src/backend/`
- [ ] AC-2: LLM format errors trigger Instructor auto-retry up to 3 times
- [ ] AC-3: `model_config.json` contains all 5 keys: intent_router_primary, reviewer, gatekeeper, producer, subtask
- [ ] AC-4: Config change + restart causes all agents to use new model names
- [ ] AC-5: All LLM calls go through a single `llm_service` entry point using LiteLLM

## Verification Commands
```bash
pytest tests/unit/backend-core/test_spec_c_011.py -v
ruff check src/backend/services/llm_service.py
mypy src/backend/services/llm_service.py --strict
grep -r "openai.ChatCompletion" src/backend/ && echo "FAIL: direct openai call found" || echo "PASS: no direct openai calls"
```

## Completion Definition
Unified LLM service using LiteLLM + Instructor. Model routing config with all 5 keys. No direct OpenAI calls. Retry logic works. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/backend-core/test_spec_c_011.py | test_no_direct_openai_calls |
| AC-2 | tests/unit/backend-core/test_spec_c_011.py | test_instructor_retries_on_format_error |
| AC-3 | tests/unit/backend-core/test_spec_c_011.py | test_model_config_has_five_keys |
| AC-4 | tests/unit/backend-core/test_spec_c_011.py | test_config_change_applies_new_model |
| AC-5 | tests/unit/backend-core/test_spec_c_011.py | test_all_calls_through_llm_service |
