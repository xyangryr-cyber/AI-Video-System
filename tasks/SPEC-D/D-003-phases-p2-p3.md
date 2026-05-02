# [SPEC-D-003] Phase P2-P3: Script & Polish Producers, Reviewers, Gates

## Metadata
- **task_id**: SPEC-D-003
- **spec_ref**: SPEC-9.2 (P2), SPEC-9.3 (P3), SPEC-9.2.4
- **depends_on**: [SPEC-D-002]
- **priority**: P0
- **estimated_complexity**: L

## Scope
Implement P2 (ScriptAgent + FactChecker + Gate-P2) and P3 (PolishAgent + Gate-P3 with integrated L1 style checks). P2 produces per-segment oral scripts with key_data_points (trust_level), enforces LLM data point limit (<=5), and maintains outline fidelity. FactChecker performs L1 source reachability + L2 semantic comparison. SPEC-9.2.4 implements automatic data point re-extraction on script revision/regenerate. P3 produces polished script with voice_direction (6 sub-fields) and is the authoritative text source. Gate-P3 includes 8 L1 programmatic style pre-checks (inheriting from deleted StyleReviewer) plus standard gate checks.

## Allowed Files
- `src/backend/agents/script_agent.py`
- `src/backend/agents/polish_agent.py`
- `src/backend/agents/reviewers/fact_checker.py`
- `src/backend/engine/gates/gate_p2.py`
- `src/backend/engine/gates/gate_p3.py`
- `src/backend/engine/style_precheck.py`
- `tests/unit/pipeline/test_script_agent.py`
- `tests/unit/pipeline/test_polish_agent.py`
- `tests/unit/pipeline/test_fact_checker.py`
- `tests/unit/pipeline/test_gate_p2.py`
- `tests/unit/pipeline/test_gate_p3.py`
- `tests/unit/pipeline/test_style_precheck.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**`
- `src/shared/schemas/**`

## Acceptance Criteria
- [ ] AC-1: ScriptAgent outputs per-segment scripts with all required fields (segment_id, section_title, outline_section_ref, content, word_count, key_data_points, emotion_tone, transition_note)
- [ ] AC-2: trust_level in {user_verified, source_verified, llm_generated}; llm_generated data points <= 5 total
- [ ] AC-3: Total word count within target_word_count +/- 10%; no new viewpoints beyond outline; no omitted outline viewpoints; every data point has non-empty source
- [ ] AC-4: FactChecker L1 checks source reachability, L2 semantic comparison; llm_generated unconfirmed data points block Gate-P2
- [ ] AC-5: Gate-P2 checks: script fields complete, FactChecker PASS, StructureReviewer PASS, no pending tasks, preferences confirmed
- [ ] AC-6: SPEC-9.2.4 re-extraction: on user_revision/regenerate, new data points get trust_level=llm_generated, changed points reset to llm_generated, unchanged points retain original trust_level, deleted points removed
- [ ] AC-7: PolishAgent outputs polished_script with voice_direction (emotion/pace/energy/key_emphasis/pause_after/notes) per segment; is_authoritative_text_source=true
- [ ] AC-8: Gate-P3 L1 style precheck (8 rules, pure code, 0 LLM tokens): person consistency, modal particle frequency [0.5-3.0]/100chars, sentence length <=80 chars, paragraph length <=300 chars (warning only), banned words list (17 words), total word count +/-5%, viewpoint count preservation, data point ID set preservation
- [ ] AC-9: Gate-P3 rejects on any L1 precheck FAIL or missing artifact

## Verification Commands
```bash
pytest tests/unit/pipeline/test_spec_d_003.py -v
```

## Completion Definition
ScriptAgent, PolishAgent, FactChecker, data point re-extraction logic, and both gates are implemented. Gate-P3 style precheck is pure code with no LLM calls. All 8 style rules are enforced. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/pipeline/test_spec_d_003.py | test_segment_has_all_fields |
| AC-2 | tests/unit/pipeline/test_spec_d_003.py | test_trust_level_enum_valid |
| AC-2 | tests/unit/pipeline/test_spec_d_003.py | test_llm_generated_data_points_max_5 |
| AC-3 | tests/unit/pipeline/test_spec_d_003.py | test_word_count_within_target_range |
| AC-3 | tests/unit/pipeline/test_spec_d_003.py | test_no_new_viewpoints_beyond_outline |
| AC-3 | tests/unit/pipeline/test_spec_d_003.py | test_data_point_source_non_empty |
| AC-4 | tests/unit/pipeline/test_spec_d_003.py | test_l1_source_reachability |
| AC-4 | tests/unit/pipeline/test_spec_d_003.py | test_llm_generated_unconfirmed_blocks_gate |
| AC-5 | tests/unit/pipeline/test_spec_d_003.py | test_gate_p2_pass |
| AC-5 | tests/unit/pipeline/test_spec_d_003.py | test_gate_p2_fail_unconfirmed_data |
| AC-6 | tests/unit/pipeline/test_spec_d_003.py | test_reextraction_new_point_llm_generated |
| AC-6 | tests/unit/pipeline/test_spec_d_003.py | test_reextraction_changed_point_reset |
| AC-6 | tests/unit/pipeline/test_spec_d_003.py | test_reextraction_unchanged_point_retained |
| AC-6 | tests/unit/pipeline/test_spec_d_003.py | test_reextraction_deleted_point_removed |
| AC-7 | tests/unit/pipeline/test_spec_d_003.py | test_voice_direction_6_subfields |
| AC-7 | tests/unit/pipeline/test_spec_d_003.py | test_authoritative_text_source_flag |
| AC-8 | tests/unit/pipeline/test_spec_d_003.py | test_person_consistency_fail |
| AC-8 | tests/unit/pipeline/test_spec_d_003.py | test_modal_particle_frequency_out_of_range |
| AC-8 | tests/unit/pipeline/test_spec_d_003.py | test_sentence_over_80_chars_fail |
| AC-8 | tests/unit/pipeline/test_spec_d_003.py | test_banned_word_detected_fail |
| AC-8 | tests/unit/pipeline/test_spec_d_003.py | test_word_count_exceeds_5_percent_fail |
| AC-8 | tests/unit/pipeline/test_spec_d_003.py | test_viewpoint_count_mismatch_fail |
| AC-8 | tests/unit/pipeline/test_spec_d_003.py | test_data_point_id_set_mismatch_fail |
| AC-8 | tests/unit/pipeline/test_spec_d_003.py | test_no_llm_calls_in_precheck |
| AC-9 | tests/unit/pipeline/test_spec_d_003.py | test_gate_p3_pass |
| AC-9 | tests/unit/pipeline/test_spec_d_003.py | test_gate_p3_fail_style_precheck |
