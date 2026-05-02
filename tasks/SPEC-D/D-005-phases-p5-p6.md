# [SPEC-D-005] Phase P5-P6: BGM & SFX Producers, Reviewers, Gates

## Metadata
- **task_id**: SPEC-D-005
- **spec_ref**: SPEC-9.5 (P5), SPEC-9.6 (P6)
- **depends_on**: [SPEC-D-004]
- **priority**: P1
- **estimated_complexity**: L
- **bdd_tags**: [@phase5, @phase6]

## Scope
Implement P5 (BGMAgent + MusicFitReviewer + Gate-P5) and P6 (SFXAgent + SFXReviewer + Gate-P6). Both phases are skippable. BGMAgent generates emotion_curve.json, recommends 3 BGM candidates via CandidateSelector, designs volume envelopes per segment type, implements 2-level source fallback, and tracks copyright. SFXAgent implements dual type system (functional + semantic), outputs per-SFX schema, enforces spacing/diversity/non-overlap constraints, and implements 3-level source fallback. MusicFitReviewer uses L1+L2, SFXReviewer is pure L1.

## Allowed Files
- `src/backend/agents/bgm_agent.py`
- `src/backend/agents/sfx_agent.py`
- `src/backend/agents/reviewers/music_fit_reviewer.py`
- `src/backend/agents/reviewers/sfx_reviewer.py`
- `src/backend/engine/gates/gate_p5.py`
- `src/backend/engine/gates/gate_p6.py`
- `tests/unit/pipeline/test_bgm_agent.py`
- `tests/unit/pipeline/test_sfx_agent.py`
- `tests/unit/pipeline/test_music_fit_reviewer.py`
- `tests/unit/pipeline/test_sfx_reviewer.py`
- `tests/unit/pipeline/test_gate_p5.py`
- `tests/unit/pipeline/test_gate_p6.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**`
- `src/shared/schemas/**`

## Acceptance Criteria
- [ ] AC-1: BGMAgent produces emotion_curve.json with per-segment emotion label + energy value (1-10) + transition point markers
- [ ] AC-2: BGM 3 candidates via CandidateSelector; recommendations correlated with emotion curve (not random)
- [ ] AC-3: BGM volume envelope: Hook <= -12dB, body <= -20dB, transition <= -14dB, body BGM does not mask voice (<= -18dB)
- [ ] AC-4: BGM 2-level fallback: Mubert API -> local library (>=10); fallback logged with source_attempted/reason_failed/source_used
- [ ] AC-5: BGM copyright marking: each candidate tagged CC0/CC-BY/proprietary
- [ ] AC-6: MusicFitReviewer L1 (0 token): BGM duration >= video total, body volume <= -18dB, copyright tag valid; L2 (LLM, only after L1 all pass): emotion style matching
- [ ] AC-7: Gate-P5 (not skipped): BGM JSON + file exist + playable, MusicFitReviewer PASS, no pending tasks, preferences confirmed; skipped: only checks no pending tasks + preferences confirmed
- [ ] AC-8: SFXAgent outputs per-SFX (sfx_id/type/semantic_type/timestamp_seconds/trigger_text/reason/volume_db/duration_seconds/file_path); dual type mapping (boom<->reveal, whoosh<->contrast, ding<->rise_positive, rise<->rise_positive, warm_pad<->drop_negative)
- [ ] AC-9: SFX constraints: average interval >= 15s, >= 3 different types, SFX+BGM combined <= narration -6dB, no overlap with BGM transition points (+/-2s)
- [ ] AC-10: SFX 3-level fallback: built-in (>=50) -> Freesound CC0 -> user upload
- [ ] AC-11: SFXReviewer pure L1 (0 token): density, type diversity, voice masking, BGM overlap, file completeness
- [ ] AC-12: Gate-P6 (not skipped): SFX JSON + files exist + playable, SFXReviewer PASS, no pending tasks, preferences confirmed; skipped: only checks no pending tasks + preferences confirmed
- [ ] AC-13: After 3 consecutive SFX reviewer FAILs -> suggest user skip P6

## Verification Commands
```bash
pytest tests/unit/pipeline/test_spec_d_005.py -v
```

## Completion Definition
BGMAgent and SFXAgent with all capabilities implemented. Emotion curve drives BGM selection. SFX dual type system with mapping table. Both reviewers enforce all checks. Gates handle both normal and skip branches. Fallback chains work with logging. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/pipeline/test_spec_d_005.py | test_emotion_curve_per_segment |
| AC-2 | tests/unit/pipeline/test_spec_d_005.py | test_candidates_correlated_with_emotion |
| AC-3 | tests/unit/pipeline/test_spec_d_005.py | test_volume_envelope_per_segment_type |
| AC-4 | tests/unit/pipeline/test_spec_d_005.py | test_fallback_mubert_to_local |
| AC-5 | tests/unit/pipeline/test_spec_d_005.py | test_copyright_marking |
| AC-6 | tests/unit/pipeline/test_spec_d_005.py | test_l1_duration_insufficient_fail |
| AC-6 | tests/unit/pipeline/test_spec_d_005.py | test_l1_volume_too_high_fail |
| AC-6 | tests/unit/pipeline/test_spec_d_005.py | test_l1_pass_triggers_l2 |
| AC-6 | tests/unit/pipeline/test_spec_d_005.py | test_l1_fail_skips_l2_zero_tokens |
| AC-7 | tests/unit/pipeline/test_spec_d_005.py | test_gate_p5_pass |
| AC-7 | tests/unit/pipeline/test_spec_d_005.py | test_gate_p5_skipped_pass |
| AC-7 | tests/unit/pipeline/test_spec_d_005.py | test_gate_p5_fail_unplayable_bgm |
| AC-8 | tests/unit/pipeline/test_spec_d_005.py | test_sfx_output_all_fields |
| AC-8 | tests/unit/pipeline/test_spec_d_005.py | test_type_semantic_type_mapping |
| AC-9 | tests/unit/pipeline/test_spec_d_005.py | test_interval_constraint |
| AC-9 | tests/unit/pipeline/test_spec_d_005.py | test_type_diversity_constraint |
| AC-9 | tests/unit/pipeline/test_spec_d_005.py | test_no_bgm_transition_overlap |
| AC-10 | tests/unit/pipeline/test_spec_d_005.py | test_fallback_builtin_to_freesound |
| AC-11 | tests/unit/pipeline/test_spec_d_005.py | test_sfx_reviewer_pure_l1_no_llm |
| AC-11 | tests/unit/pipeline/test_spec_d_005.py | test_density_too_high_fail |
| AC-11 | tests/unit/pipeline/test_spec_d_005.py | test_voice_masking_fail |
| AC-12 | tests/unit/pipeline/test_spec_d_005.py | test_gate_p6_pass |
| AC-12 | tests/unit/pipeline/test_spec_d_005.py | test_gate_p6_skipped_pass |
| AC-13 | tests/unit/pipeline/test_spec_d_005.py | test_3_consecutive_fails_suggest_skip |
