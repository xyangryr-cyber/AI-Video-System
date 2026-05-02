# [SPEC-D-017] Phase Scenario Cards & Failure Recovery Paths

## Metadata
- **task_id**: SPEC-D-017
- **spec_ref**: SPEC-9.12, SPEC-D failure recovery table
- **depends_on**: [SPEC-D-002, SPEC-D-003, SPEC-D-004, SPEC-D-005, SPEC-D-006, SPEC-D-007, SPEC-D-008, SPEC-D-009, SPEC-D-012]
- **priority**: P1
- **estimated_complexity**: M

## Scope
Implement the phase scenario cards (SPEC-9.12) and the minimum recovery path table for all 12 phases. Each phase has specific exception handling rules beyond the generic 5x regenerate limit. This includes: per-phase retry limits, skip suggestions, rollback cascades (e.g., P7 rollback to P2 invalidates P3-P7), freeze-and-manual-edit mode, auto-retry with provider switch, and session recovery (browser close/reopen within 10s). The recovery logic integrates with FSM state management to handle phase invalidation cascades.

## Allowed Files
- `src/backend/engine/failure_recovery.py`
- `src/backend/engine/phase_scenarios.py`
- `src/backend/engine/rollback_cascade.py`
- `tests/unit/pipeline/test_failure_recovery.py`
- `tests/unit/pipeline/test_phase_scenarios.py`
- `tests/unit/pipeline/test_rollback_cascade.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**`
- `src/shared/schemas/**`

## Acceptance Criteria
- [ ] AC-1: P0 scenarios: description < 300 chars -> prompt user supplement; 5 consecutive revise failures -> suggest rewrite initial input
- [ ] AC-2: P1 scenarios: 5 consecutive regenerate -> suggest return to P0; no infinite retry
- [ ] AC-3: P3 scenarios: 5 polish iterations -> freeze current version + offer manual edit mode
- [ ] AC-4: P4 scenarios: TTS failure -> auto-retry (max 3) -> switch TTSProvider -> manual retry; browser close/reopen recovery within 10s
- [ ] AC-5: P5 scenarios: copyright block -> auto-switch source 1x -> suggest skip P5
- [ ] AC-6: P6 scenarios: 3 consecutive SFX reviewer FAILs -> suggest skip P6
- [ ] AC-7: P7 rollback cascade: rollback to P2 -> P3-P7 all set to status=invalidated
- [ ] AC-8: P8 scenarios: partial frame corruption -> mark invalid, re-render only damaged frames; success rate >= 90% still passes
- [ ] AC-9: P9 scenarios: copyright block -> auto-switch source 1x -> if still blocked, record gap, BRollFitReviewer must FAIL
- [ ] AC-10: P11 scenarios: 2 consecutive export failures -> stop auto-retry, show manual retry button; rollback to P2 -> P3-P11 invalidated with "estimated 30-45 min redo" prompt
- [ ] AC-11: Rollback cascade engine: given rollback target phase, correctly invalidates all downstream phases and resets their artifacts
- [ ] AC-12: All scenario rules registered in a lookup table indexed by phase number + scenario type

## Verification Commands
```bash
pytest tests/unit/pipeline/test_spec_d_017.py -v
```

## Completion Definition
All 12 phase scenario rules implemented with correct retry limits, skip suggestions, and recovery paths. Rollback cascade correctly invalidates downstream phases. Scenario lookup table covers all defined cases. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/pipeline/test_spec_d_017.py | test_p0_short_description_prompt |
| AC-1 | tests/unit/pipeline/test_spec_d_017.py | test_p0_5_revise_suggest_rewrite |
| AC-2 | tests/unit/pipeline/test_spec_d_017.py | test_p1_5_regenerate_suggest_p0 |
| AC-3 | tests/unit/pipeline/test_spec_d_017.py | test_p3_5_iterations_freeze_manual |
| AC-4 | tests/unit/pipeline/test_spec_d_017.py | test_p4_tts_auto_retry_max_3 |
| AC-4 | tests/unit/pipeline/test_spec_d_017.py | test_p4_switch_provider_on_retry_exhaust |
| AC-4 | tests/unit/pipeline/test_spec_d_017.py | test_p4_session_recovery_10s |
| AC-5 | tests/unit/pipeline/test_spec_d_017.py | test_p5_copyright_auto_switch |
| AC-5 | tests/unit/pipeline/test_spec_d_017.py | test_p5_suggest_skip |
| AC-6 | tests/unit/pipeline/test_spec_d_017.py | test_p6_3_fails_suggest_skip |
| AC-7 | tests/unit/pipeline/test_spec_d_017.py | test_p7_rollback_to_p2_invalidates_p3_p7 |
| AC-8 | tests/unit/pipeline/test_spec_d_017.py | test_p8_partial_rerender |
| AC-9 | tests/unit/pipeline/test_spec_d_017.py | test_p9_copyright_block_reviewer_fail |
| AC-10 | tests/unit/pipeline/test_spec_d_017.py | test_p11_2_failures_stop_auto_retry |
| AC-10 | tests/unit/pipeline/test_spec_d_017.py | test_p11_rollback_to_p2_invalidates_p3_p11 |
| AC-11 | tests/unit/pipeline/test_spec_d_017.py | test_cascade_invalidates_downstream |
| AC-11 | tests/unit/pipeline/test_spec_d_017.py | test_cascade_resets_artifacts |
| AC-12 | tests/unit/pipeline/test_spec_d_017.py | test_scenario_lookup_all_phases |
