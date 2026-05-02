# [SPEC-C-106] IntentRouter BDD POC

## Metadata
- **task_id**: SPEC-C-106
- **spec_ref**: BDD §IntentRouter (docs/BDD_ai_system_expected_behavior_v1.feature.md)
- **depends_on**: []
- **priority**: P2
- **estimated_complexity**: S
- **allowed_files**: [src/backend/agents/intent_router.py, tests/integration/bdd/steps/router_steps.py]
- **bdd_tags**: [@router]

## Scope
Keep the IntentRouter BDD POC (1 scenario) green. This card is the owner
for all @router BDD scenarios; expanding scenario coverage is a follow-up.

## Acceptance Criteria
- [ ] AC-1: `pytest tests/integration/bdd/ -m router` passes at least one scenario
- [ ] AC-2: Fallback behaviour: invalid JSON -> action=clarify, events contains `router.intent_fallback`

## Verification Commands
```bash
pytest tests/integration/bdd/ -m router -v
```

## Completion Definition
`@router` tag has at least the timeout/fallback scenario green; CI will keep it green via Loop auto-invocation (Task 7 of plan).
