# [SPEC-D-004] Phase P4: TTS Producer, AudioQualityReviewer, Gate

## Metadata
- **task_id**: SPEC-D-004
- **spec_ref**: SPEC-9.4 (P4)
- **depends_on**: [SPEC-D-003]
- **priority**: P0
- **estimated_complexity**: L
- **bdd_tags**: [@phase4]

## Scope
Implement P4 TTSAgent (async), AudioQualityReviewer, and Gate-P4. TTSAgent is the most complex producer with 8 core capabilities: preference voice priority, new voice preference confirmation, global voice params, segment voice overrides, voice direction bridging (from P3), digit-aware slowdown (SSML), TTSProvider abstraction layer, and timeline.json production. AudioQualityReviewer checks CPS range, silence/clipping, timeline accuracy, segment gaps, file playability, total duration, and sample rate. Gate-P4 enforces audio file existence, reviewer PASS, async task completion, and preferences confirmation.

## Allowed Files
- `src/backend/agents/tts_agent.py`
- `src/backend/agents/reviewers/audio_quality_reviewer.py`
- `src/backend/engine/gates/gate_p4.py`
- `src/backend/services/tts_provider.py`
- `src/backend/services/voice_direction_bridge.py`
- `src/backend/services/digit_slowdown.py`
- `tests/unit/pipeline/test_tts_agent.py`
- `tests/unit/pipeline/test_audio_quality_reviewer.py`
- `tests/unit/pipeline/test_gate_p4.py`
- `tests/unit/pipeline/test_voice_direction_bridge.py`
- `tests/unit/pipeline/test_digit_slowdown.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**`
- `src/shared/schemas/**`

## Acceptance Criteria
- [ ] AC-1: With voice preference, candidates list preferred voice first with is_recommended=true; generates 1 preferred + 1-2 recommended 15s previews
- [ ] AC-2: Without voice preference, generates 2-3 candidate 15s(+/-0.5s) previews via CandidateSelector
- [ ] AC-3: User selects non-preferred voice -> confirmation prompt; accept writes to user_preferences_md, reject writes to project_preferences_md
- [ ] AC-4: global_voice_params contains voice_id + style + style_degree + rate_wpm + pitch + volume
- [ ] AC-5: segment_voice_overrides per segment (rate_multiplier/emotion/volume/emphasis_words); priority: segment override > digit slowdown > global rate_wpm
- [ ] AC-6: voice_direction -> segment_voice_overrides conversion is pure code (0 LLM tokens)
- [ ] AC-7: Digit-dense sentences detected by regex, wrapped with SSML `<prosody rate="slow">` + `<break>` tags
- [ ] AC-8: TTSProvider abstraction: synthesize(text, ssml_tags, voice_params) -> AudioResult; unsupported params logged as capability_gap; provider switch requires no upstream code change
- [ ] AC-9: timeline.json output with segments[].start_sec/end_sec/audio_path/voice_params/word_count + total_duration_sec + sample_rate; timestamps continuous with no gaps
- [ ] AC-10: AudioQualityReviewer checks: CPS in [3.0, 5.0], no silence >2s or clipping, timeline vs audio error <=50ms/segment, inter-segment silence in [0.3s, 0.8s], all files playable, total duration vs target <=20%, sample_rate=44100
- [ ] AC-11: Gate-P4 checks: all segment audio files exist + playable, AudioQualityReviewer PASS, TTS async_task done, no pending tasks, preferences confirmed

## Verification Commands
```bash
pytest tests/unit/pipeline/test_spec_d_004.py -v
```

## Completion Definition
TTSAgent with all 8 capabilities is implemented. Voice direction bridge and digit slowdown are pure code. TTSProvider abstraction allows provider switching without upstream changes. AudioQualityReviewer validates all 7 quality criteria. Gate-P4 enforces all 5 checks. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/pipeline/test_spec_d_004.py | test_preferred_voice_first_with_recommended |
| AC-2 | tests/unit/pipeline/test_spec_d_004.py | test_no_preference_generates_2_to_3_previews |
| AC-3 | tests/unit/pipeline/test_spec_d_004.py | test_new_voice_confirmation_accept |
| AC-3 | tests/unit/pipeline/test_spec_d_004.py | test_new_voice_confirmation_reject |
| AC-4 | tests/unit/pipeline/test_spec_d_004.py | test_global_voice_params_complete |
| AC-5 | tests/unit/pipeline/test_spec_d_004.py | test_segment_override_priority |
| AC-6 | tests/unit/pipeline/test_spec_d_004.py | test_bridge_is_pure_code_no_llm |
| AC-6 | tests/unit/pipeline/test_spec_d_004.py | test_bridge_maps_all_directions |
| AC-7 | tests/unit/pipeline/test_spec_d_004.py | test_digit_dense_detection |
| AC-7 | tests/unit/pipeline/test_spec_d_004.py | test_ssml_prosody_wrapping |
| AC-8 | tests/unit/pipeline/test_spec_d_004.py | test_provider_abstraction_interface |
| AC-8 | tests/unit/pipeline/test_spec_d_004.py | test_capability_gap_logged |
| AC-9 | tests/unit/pipeline/test_spec_d_004.py | test_timeline_json_continuous_timestamps |
| AC-10 | tests/unit/pipeline/test_spec_d_004.py | test_cps_out_of_range_fail |
| AC-10 | tests/unit/pipeline/test_spec_d_004.py | test_silence_over_2s_fail |
| AC-10 | tests/unit/pipeline/test_spec_d_004.py | test_timeline_audio_mismatch_fail |
| AC-10 | tests/unit/pipeline/test_spec_d_004.py | test_segment_gap_out_of_range_fail |
| AC-10 | tests/unit/pipeline/test_spec_d_004.py | test_sample_rate_not_44100_fail |
| AC-11 | tests/unit/pipeline/test_spec_d_004.py | test_gate_p4_pass |
| AC-11 | tests/unit/pipeline/test_spec_d_004.py | test_gate_p4_fail_missing_audio |
| AC-11 | tests/unit/pipeline/test_spec_d_004.py | test_gate_p4_fail_async_running |
