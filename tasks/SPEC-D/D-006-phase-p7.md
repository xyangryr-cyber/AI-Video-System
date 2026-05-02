# [SPEC-D-006] Phase P7: Storyboard Producer, Reviewer, Gate

## Metadata
- **task_id**: SPEC-D-006
- **spec_ref**: SPEC-9.7 (P7)
- **depends_on**: [SPEC-D-005]
- **priority**: P0
- **estimated_complexity**: L

## Scope
Implement P7 StoryboardAgent, StoryboardReviewer, and Gate-P7. StoryboardAgent produces storyboard JSON with shot-level detail, supports template/broll dual shot types, animation_keyframes dual modes, data visualization coverage >= 80%, style_lock generation/locking flow (3 candidates via CandidateSelector), and cross-phase audit #1. StoryboardReviewer performs L1 programmatic checks (time coverage, switch frequency, shot duration, data coverage, time alignment) + L2 LLM narrative alignment. Gate-P7 enforces storyboard completeness, style_lock existence, reviewer PASS, and audit #1 clean.

## Allowed Files
- `src/backend/agents/storyboard_agent.py`
- `src/backend/agents/reviewers/storyboard_reviewer.py`
- `src/backend/engine/gates/gate_p7.py`
- `src/backend/engine/cross_phase_audit.py`
- `tests/unit/pipeline/test_storyboard_agent.py`
- `tests/unit/pipeline/test_storyboard_reviewer.py`
- `tests/unit/pipeline/test_gate_p7.py`
- `tests/unit/pipeline/test_cross_phase_audit.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**`
- `src/shared/schemas/**`

## Acceptance Criteria
- [ ] AC-1: StoryboardAgent outputs shots with all fields (shot_id, time_range.start/end_seconds, type=template|broll, template_type, search_keywords, content, narration_text, data_point_refs[])
- [ ] AC-2: Data visualization coverage: covered_key_data_points / total >= 80%; each key_data_point has at least 1 chart/data card
- [ ] AC-3: style_lock flow: 3 color scheme candidates via CandidateSelector -> user confirms -> writes style_lock.json -> updates phases.style_lock_path; unlock = rollback to P7
- [ ] AC-4: Shot timing constraints: single shot duration in [3s, 30s], consecutive same-type shots <= 2, all shots cover timeline continuously with no gaps, every 30s window has at least 1 scene switch
- [ ] AC-5: Each shot's narration_text aligned with timeline segment time window
- [ ] AC-6: Cross-phase audit #1: script data vs storyboard data points (every shot data_point_id exists in P2 key_data_points), segment time vs shot time alignment, INCONSISTENCY count = 0
- [ ] AC-7: StoryboardReviewer L1 (0 token): time coverage, switch frequency (<=2 consecutive same type), shot duration [3s,30s], data coverage (every data_point referenced), time alignment (>=80% overlap); L2 (LLM, only after L1 pass): narrative alignment
- [ ] AC-8: Gate-P7 checks: storyboard JSON complete, style_lock.json exists, StoryboardReviewer PASS, audit #1 INCONSISTENCY=0, no pending tasks, preferences confirmed
- [ ] AC-9: Visual preference input: when user has visual preferences, color scheme candidates match preferences

## Verification Commands
```bash
pytest tests/unit/pipeline/test_spec_d_006.py -v
```

## Completion Definition
StoryboardAgent with all capabilities, style_lock flow, and cross-phase audit #1 implemented. StoryboardReviewer L1 checks are pure code. Gate-P7 enforces all 6 checks including audit result. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/pipeline/test_spec_d_006.py | test_shot_has_all_fields |
| AC-2 | tests/unit/pipeline/test_spec_d_006.py | test_data_visualization_coverage_80_percent |
| AC-2 | tests/unit/pipeline/test_spec_d_006.py | test_each_data_point_has_visual |
| AC-3 | tests/unit/pipeline/test_spec_d_006.py | test_style_lock_3_candidates |
| AC-3 | tests/unit/pipeline/test_spec_d_006.py | test_style_lock_user_confirm_writes_json |
| AC-4 | tests/unit/pipeline/test_spec_d_006.py | test_shot_duration_in_range |
| AC-4 | tests/unit/pipeline/test_spec_d_006.py | test_consecutive_same_type_max_2 |
| AC-4 | tests/unit/pipeline/test_spec_d_006.py | test_shots_continuous_no_gaps |
| AC-4 | tests/unit/pipeline/test_spec_d_006.py | test_scene_switch_every_30s |
| AC-5 | tests/unit/pipeline/test_spec_d_006.py | test_narration_text_timeline_alignment |
| AC-6 | tests/unit/pipeline/test_spec_d_006.py | test_audit_1_data_point_ids_valid |
| AC-6 | tests/unit/pipeline/test_spec_d_006.py | test_audit_1_time_alignment |
| AC-6 | tests/unit/pipeline/test_spec_d_006.py | test_audit_1_inconsistency_zero |
| AC-7 | tests/unit/pipeline/test_spec_d_006.py | test_l1_time_gap_fail |
| AC-7 | tests/unit/pipeline/test_spec_d_006.py | test_l1_3_consecutive_same_type_fail |
| AC-7 | tests/unit/pipeline/test_spec_d_006.py | test_l1_shot_duration_2s_fail |
| AC-7 | tests/unit/pipeline/test_spec_d_006.py | test_l1_uncovered_data_point_fail |
| AC-7 | tests/unit/pipeline/test_spec_d_006.py | test_l1_pass_triggers_l2 |
| AC-7 | tests/unit/pipeline/test_spec_d_006.py | test_l1_fail_skips_l2_zero_tokens |
| AC-8 | tests/unit/pipeline/test_spec_d_006.py | test_gate_p7_pass |
| AC-8 | tests/unit/pipeline/test_spec_d_006.py | test_gate_p7_fail_no_style_lock |
| AC-8 | tests/unit/pipeline/test_spec_d_006.py | test_gate_p7_fail_audit_inconsistency |
| AC-9 | tests/unit/pipeline/test_spec_d_006.py | test_candidates_match_visual_preferences |
