# [SPEC-D-012] Unified Gate Checking Framework

## Metadata
- **task_id**: SPEC-D-012
- **spec_ref**: SPEC-D Reviewer/Gate/Verdict unified binding, SPEC-C SPEC-8.1
- **depends_on**: [SPEC-D-001, SPEC-C-005]
- **priority**: P0
- **estimated_complexity**: M
- **bdd_tags**: [@gatekeeper]

## Scope
Implement the unified gate checking framework that all 12 phase gates (Gate-P0 through Gate-P11) inherit from. The framework standardizes: gate check registration, sequential execution of check items, result format (`{failed_checks[], passed_checks[]}`), EVID_2001 error response on failure, integration with GateKeeper (SPEC-C SPEC-8.1), skip-branch handling for optional phases (P5, P6), async task completion checking, preferences_confirmed_at validation, and artifact_status validation. Each phase-specific gate registers its check items but the execution/response logic is shared.

## Allowed Files
- `src/backend/engine/gates/base_gate.py`
- `src/backend/engine/gates/gate_registry.py`
- `tests/unit/pipeline/test_base_gate.py`
- `tests/unit/pipeline/test_gate_registry.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**`
- `src/shared/schemas/**`

## Acceptance Criteria
- [ ] AC-1: BaseGate abstract class with `check(project_state) -> GateResult` method; GateResult contains passed_checks[] and failed_checks[]
- [ ] AC-2: Gate check items registered via list; each check is a callable returning (pass: bool, check_name: str, detail: str)
- [ ] AC-3: Common check helpers: artifact_exists(path), artifact_schema_valid(path, schema), reviewer_passed(reviewer_name), no_pending_tasks(), preferences_confirmed(), async_task_done(task_type)
- [ ] AC-4: Gate failure returns EVID_2001 error code with full check results
- [ ] AC-5: Skip-branch support: when phase status=skipped, only checks no_pending_tasks + preferences_confirmed (for P5, P6)
- [ ] AC-6: Gate pass triggers FSM advance (integrates with GateKeeper from SPEC-C)
- [ ] AC-7: GateRegistry maps phase number to gate class; lookup by phase returns correct gate

## Verification Commands
```bash
pytest tests/unit/pipeline/test_spec_d_012.py -v
mypy src/backend/engine/gates/base_gate.py --strict
```

## Completion Definition
BaseGate and GateRegistry implemented. Common check helpers cover all standard gate items. Skip-branch logic works for optional phases. EVID_2001 error response generated on failure. FSM advance integration point defined. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/pipeline/test_spec_d_012.py | test_base_gate_is_abstract |
| AC-1 | tests/unit/pipeline/test_spec_d_012.py | test_gate_result_structure |
| AC-2 | tests/unit/pipeline/test_spec_d_012.py | test_register_check_items |
| AC-3 | tests/unit/pipeline/test_spec_d_012.py | test_artifact_exists_helper |
| AC-3 | tests/unit/pipeline/test_spec_d_012.py | test_reviewer_passed_helper |
| AC-3 | tests/unit/pipeline/test_spec_d_012.py | test_no_pending_tasks_helper |
| AC-3 | tests/unit/pipeline/test_spec_d_012.py | test_preferences_confirmed_helper |
| AC-3 | tests/unit/pipeline/test_spec_d_012.py | test_async_task_done_helper |
| AC-4 | tests/unit/pipeline/test_spec_d_012.py | test_failure_returns_evid_2001 |
| AC-5 | tests/unit/pipeline/test_spec_d_012.py | test_skip_branch_minimal_checks |
| AC-6 | tests/unit/pipeline/test_spec_d_012.py | test_pass_triggers_advance |
| AC-7 | tests/unit/pipeline/test_spec_d_012.py | test_registry_maps_all_12_phases |
| AC-7 | tests/unit/pipeline/test_spec_d_012.py | test_lookup_by_phase_number |
