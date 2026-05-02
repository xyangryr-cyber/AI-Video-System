# [SPEC-C-006] IntentRouter Core (Stateless Design + Context Injection + Model Config)

## Metadata
- **task_id**: SPEC-C-006
- **spec_ref**: SPEC-4.1, SPEC-4.2, SPEC-4.3
- **depends_on**: [SPEC-A-001, SPEC-C-001]
- **priority**: P0
- **estimated_complexity**: M

## Scope
Implement the IntentRouter as a stateless class: each call reads all context from SQLite (no cross-call instance state). Build the fixed context injection template (system prompt + project meta + artifact snapshot <=2000 tokens + ledger summary <=800 tokens + last 6 conversations + preference rules <=20/1200 tokens + available actions + user input). Model comes from `model_config.json` key `intent_router_primary`, default `claude-haiku-4-5`. `confirm_next` must NOT appear in the action enum.

## Allowed Files
- `src/backend/agents/intent_router.py`
- `src/backend/agents/__init__.py`
- `tests/unit/backend-core/test_intent_router.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**` (owned by SPEC-A)
- `config/**` (owned by SPEC-B)

## Acceptance Criteria
- [ ] AC-1: IntentRouter class has no instance variables storing cross-call state
- [ ] AC-2: After API restart, Router is immediately usable (no warmup)
- [ ] AC-3: Artifact snapshot exceeding 2000 tokens is truncated without error
- [ ] AC-4: Conversation history takes the latest 6 entries (not oldest)
- [ ] AC-5: `confirm_next` is not in the available actions enum
- [ ] AC-6: Model name read from config, no hardcoded model string in source
- [ ] AC-7: Config change + restart causes Router to use the new model

## Verification Commands
```bash
pytest tests/unit/backend-core/test_spec_c_006.py -v
ruff check src/backend/agents/intent_router.py
mypy src/backend/agents/intent_router.py --strict
```

## Completion Definition
IntentRouter is stateless, context template is correctly assembled with all truncation rules, model is config-driven, confirm_next excluded. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/backend-core/test_spec_c_006.py | test_router_no_instance_state |
| AC-2 | tests/unit/backend-core/test_spec_c_006.py | test_router_usable_without_warmup |
| AC-3 | tests/unit/backend-core/test_spec_c_006.py | test_artifact_snapshot_truncation |
| AC-4 | tests/unit/backend-core/test_spec_c_006.py | test_conversation_latest_six |
| AC-5 | tests/unit/backend-core/test_spec_c_006.py | test_confirm_next_not_in_actions |
| AC-6 | tests/unit/backend-core/test_spec_c_006.py | test_model_from_config_not_hardcoded |
| AC-7 | tests/unit/backend-core/test_spec_c_006.py | test_model_config_change_applied |
