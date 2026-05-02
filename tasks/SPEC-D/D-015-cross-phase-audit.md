# [SPEC-D-015] Cross-Phase Audit Points

## Metadata
- **task_id**: SPEC-D-015
- **spec_ref**: SPEC-D Cross-phase audit points (Audit #1, #2, #3)
- **depends_on**: [SPEC-D-006, SPEC-D-008, SPEC-D-009]
- **priority**: P0
- **estimated_complexity**: M

## Scope
Implement the three cross-phase audit points that verify data consistency across pipeline phases. Audit #1 (P7): script data vs storyboard data points, segment time vs shot time. Audit #2 (P10): subtitle text vs polished_script text, storyboard shot time vs actual shot time, rendered data vs key_data_points. Audit #3 (P11): summary of all prior audit INCONSISTENCY records, requiring all to be resolved or accepted_deviation. All audits are pure programmatic checks (0 token). The audit framework supports INCONSISTENCY tracking with resolution status.

## Allowed Files
- `src/backend/engine/cross_phase_audit.py`
- `src/backend/engine/inconsistency_tracker.py`
- `tests/unit/pipeline/test_cross_phase_audit.py`
- `tests/unit/pipeline/test_inconsistency_tracker.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**`
- `src/shared/schemas/**`

## Acceptance Criteria
- [ ] AC-1: Audit #1 (P7): every shot data_point_id exists in P2 key_data_points; script segment count matches storyboard shot references; shot time_range aligns with timeline.json segments; number/name consistency between script and storyboard
- [ ] AC-2: Audit #1 INCONSISTENCY count must be 0 for Gate-P7 to pass
- [ ] AC-3: Audit #2 (P10): subtitle text character-by-character equals polished_script text (diff count = 0); storyboard shot time_range vs actual rough_cut shot time deviation <= 0.5s; rendered data values match key_data_points (reuses P8 cross-check); video duration vs timeline duration deviation <= 1s
- [ ] AC-4: Audit #2 INCONSISTENCY count must be 0 for Gate-P10 to pass
- [ ] AC-5: Audit #3 (P11): collects all INCONSISTENCY records from Audit #1 and #2; each must have status=resolved or status=accepted_deviation; any unresolved -> FinalReviewer FAIL
- [ ] AC-6: InconsistencyTracker stores records with: audit_id, phase, check_name, expected_value, actual_value, status (detected/resolved/accepted_deviation), resolved_at
- [ ] AC-7: All audits are pure code (0 LLM token cost)

## Verification Commands
```bash
pytest tests/unit/pipeline/test_spec_d_015.py -v
mypy src/backend/engine/cross_phase_audit.py --strict
```

## Completion Definition
Three audit points implemented with correct input files and check items per spec. InconsistencyTracker stores and manages records with resolution status. Audit #3 aggregates prior results. All audits are pure code. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/pipeline/test_spec_d_015.py | test_audit_1_data_point_ids_valid |
| AC-1 | tests/unit/pipeline/test_spec_d_015.py | test_audit_1_segment_shot_count_match |
| AC-1 | tests/unit/pipeline/test_spec_d_015.py | test_audit_1_time_alignment |
| AC-1 | tests/unit/pipeline/test_spec_d_015.py | test_audit_1_number_name_consistency |
| AC-2 | tests/unit/pipeline/test_spec_d_015.py | test_audit_1_inconsistency_blocks_gate_p7 |
| AC-3 | tests/unit/pipeline/test_spec_d_015.py | test_audit_2_subtitle_matches_script_exact |
| AC-3 | tests/unit/pipeline/test_spec_d_015.py | test_audit_2_shot_time_deviation_05s |
| AC-3 | tests/unit/pipeline/test_spec_d_015.py | test_audit_2_rendered_data_matches_key_points |
| AC-3 | tests/unit/pipeline/test_spec_d_015.py | test_audit_2_duration_deviation_1s |
| AC-4 | tests/unit/pipeline/test_spec_d_015.py | test_audit_2_inconsistency_blocks_gate_p10 |
| AC-5 | tests/unit/pipeline/test_spec_d_015.py | test_audit_3_collects_all_prior |
| AC-5 | tests/unit/pipeline/test_spec_d_015.py | test_audit_3_unresolved_fails |
| AC-5 | tests/unit/pipeline/test_spec_d_015.py | test_audit_3_all_resolved_passes |
| AC-6 | tests/unit/pipeline/test_spec_d_015.py | test_tracker_record_fields |
| AC-6 | tests/unit/pipeline/test_spec_d_015.py | test_tracker_resolve_record |
| AC-6 | tests/unit/pipeline/test_spec_d_015.py | test_tracker_accept_deviation |
| AC-7 | tests/unit/pipeline/test_spec_d_015.py | test_all_audits_zero_tokens |
