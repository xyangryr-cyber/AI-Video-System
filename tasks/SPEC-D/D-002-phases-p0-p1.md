# [SPEC-D-002] Phase P0-P1: Requirements & Outline Producers, Reviewers, Gates

## Metadata
- **task_id**: SPEC-D-002
- **spec_ref**: SPEC-9.0 (P0), SPEC-9.1 (P1)
- **depends_on**: [SPEC-D-001, SPEC-C-003, SPEC-C-005]
- **priority**: P0
- **estimated_complexity**: L

## Scope
Implement P0 (RequirementsAgent + CompletenessReviewer + Gate-P0) and P1 (OutlineAgent + StructureReviewer + Gate-P1). P0 produces `requirements.json` with all required fields including v3.10/v3.12 additions. CompletenessReviewer validates 7 field-level rules including category level1/level2 enum mapping. P1 produces 2-3 outline versions with narrative beats. StructureReviewer validates structure, duration ratios, and inter-version diversity. Gates enforce artifact existence, reviewer PASS, and preferences confirmation.

## Allowed Files
- `src/backend/agents/requirements_agent.py`
- `src/backend/agents/outline_agent.py`
- `src/backend/agents/reviewers/completeness_reviewer.py`
- `src/backend/agents/reviewers/structure_reviewer.py`
- `src/backend/engine/gates/gate_p0.py`
- `src/backend/engine/gates/gate_p1.py`
- `tests/unit/pipeline/test_requirements_agent.py`
- `tests/unit/pipeline/test_outline_agent.py`
- `tests/unit/pipeline/test_completeness_reviewer.py`
- `tests/unit/pipeline/test_structure_reviewer.py`
- `tests/unit/pipeline/test_gate_p0.py`
- `tests/unit/pipeline/test_gate_p1.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**`
- `src/shared/schemas/**`

## Acceptance Criteria
- [ ] AC-1: RequirementsAgent outputs requirements.json with all SPEC-9.0.1 fields (project_id, title, topic, duration_class, target_duration, target_word_count, platform, category, narrative_template, voice_preferences, target_platform, subtitle_preferences)
- [ ] AC-2: target_word_count and target_duration x speech_rate_baseline error <= 10%
- [ ] AC-3: CompletenessReviewer enforces all 7 FAIL conditions (topic<5chars, invalid duration_class, invalid word_count range, no valid platform, empty resolution/bitrate/format, invalid category enum, invalid narrative_template)
- [ ] AC-4: CompletenessReviewer validates category.level1->level2 enum mapping (6 level1 values, each with specific level2 values)
- [ ] AC-5: Gate-P0 checks: requirements.json exists + schema valid, CompletenessReviewer PASS, preferences_confirmed_at non-null
- [ ] AC-6: OutlineAgent produces 2-3 versions, each with 5 narrative_beats (hook/context/argument/climax/conclusion), non-overlapping time intervals, transition_to_next fields, supporting_data per viewpoint, estimated_word_count in range
- [ ] AC-7: StructureReviewer validates opening+body(>=2)+closing, duration_ratio sum=1.0(+-0.05), inter-version diversity (at least 1 of 3 conditions), transition_to_next non-empty
- [ ] AC-8: Gate-P1 checks: selected outline exists + JSON valid, StructureReviewer PASS on selected version, artifact_ref matches user selection, no pending tasks, preferences confirmed
- [ ] AC-9: Gate-P1 FAIL when outline not selected or StructureReviewer FAIL

## Verification Commands
```bash
pytest tests/unit/pipeline/test_spec_d_002.py -v
```

## Completion Definition
Both P0 and P1 phase agents, reviewers, and gates are implemented. CompletenessReviewer correctly rejects all 7 invalid input categories. StructureReviewer validates structure and diversity. Gates enforce all check items. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/pipeline/test_spec_d_002.py | test_output_has_all_required_fields |
| AC-2 | tests/unit/pipeline/test_spec_d_002.py | test_word_count_duration_consistency |
| AC-3 | tests/unit/pipeline/test_spec_d_002.py | test_topic_too_short_fails |
| AC-3 | tests/unit/pipeline/test_spec_d_002.py | test_invalid_duration_class_fails |
| AC-3 | tests/unit/pipeline/test_spec_d_002.py | test_word_count_max_exceeds_limit_fails |
| AC-3 | tests/unit/pipeline/test_spec_d_002.py | test_no_valid_platform_fails |
| AC-3 | tests/unit/pipeline/test_spec_d_002.py | test_empty_resolution_fails |
| AC-3 | tests/unit/pipeline/test_spec_d_002.py | test_invalid_category_level1_fails |
| AC-3 | tests/unit/pipeline/test_spec_d_002.py | test_invalid_narrative_template_fails |
| AC-4 | tests/unit/pipeline/test_spec_d_002.py | test_category_level2_mismatch_fails |
| AC-4 | tests/unit/pipeline/test_spec_d_002.py | test_valid_category_mapping_passes |
| AC-5 | tests/unit/pipeline/test_spec_d_002.py | test_gate_p0_pass |
| AC-5 | tests/unit/pipeline/test_spec_d_002.py | test_gate_p0_fail_missing_requirements |
| AC-5 | tests/unit/pipeline/test_spec_d_002.py | test_gate_p0_fail_preferences_not_confirmed |
| AC-6 | tests/unit/pipeline/test_spec_d_002.py | test_produces_2_to_3_versions |
| AC-6 | tests/unit/pipeline/test_spec_d_002.py | test_narrative_beats_non_overlapping |
| AC-6 | tests/unit/pipeline/test_spec_d_002.py | test_supporting_data_per_viewpoint |
| AC-7 | tests/unit/pipeline/test_spec_d_002.py | test_valid_structure_passes |
| AC-7 | tests/unit/pipeline/test_spec_d_002.py | test_duration_ratio_sum_out_of_range_fails |
| AC-7 | tests/unit/pipeline/test_spec_d_002.py | test_inter_version_diversity |
| AC-8 | tests/unit/pipeline/test_spec_d_002.py | test_gate_p1_pass |
| AC-9 | tests/unit/pipeline/test_spec_d_002.py | test_gate_p1_fail_no_selection |
| AC-9 | tests/unit/pipeline/test_spec_d_002.py | test_gate_p1_fail_reviewer_fail |
