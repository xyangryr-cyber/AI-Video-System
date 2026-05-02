# [SPEC-D-008] Phase P10: RoughCut Producer, AVSyncReviewer, Gate

## Metadata
- **task_id**: SPEC-D-008
- **spec_ref**: SPEC-9.10 (P10)
- **depends_on**: [SPEC-D-007]
- **priority**: P0
- **estimated_complexity**: L
- **bdd_tags**: [@phase10]

## Scope
Implement P10 RoughCutAgent (async), AVSyncReviewer, and Gate-P10. RoughCutAgent is a complex composition agent that mixes audio (voice + BGM envelope + SFX overlay), generates subtitles via Whisper forced alignment with keyword highlighting, applies transition effects (crossfade intra-segment, hard cut + chapter title card inter-chapter), performs cross-phase audit #2, and exports H.264 video matched to target platform specs. AVSyncReviewer is pure L1 (0 token) checking AV sync, blank frames, subtitle alignment, duration, resolution, and highlight word consistency.

## Allowed Files
- `src/backend/agents/rough_cut_agent.py`
- `src/backend/agents/reviewers/av_sync_reviewer.py`
- `src/backend/engine/gates/gate_p10.py`
- `src/backend/services/audio_mixer.py`
- `src/backend/services/subtitle_generator.py`
- `src/backend/services/keyword_highlighter.py`
- `tests/unit/pipeline/test_rough_cut_agent.py`
- `tests/unit/pipeline/test_av_sync_reviewer.py`
- `tests/unit/pipeline/test_gate_p10.py`
- `tests/unit/pipeline/test_audio_mixer.py`
- `tests/unit/pipeline/test_subtitle_generator.py`
- `tests/unit/pipeline/test_keyword_highlighter.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**`
- `src/shared/schemas/**`

## Acceptance Criteria
- [ ] AC-1: Audio mixing: voice at 0dB main track, BGM per emotion_curve envelope (Hook -12dB, body -20dB, transition -14dB), SFX overlay not exceeding voice -6dB
- [ ] AC-2: Subtitle generation: Whisper forced alignment -> word-level timestamps -> subtitle_words[] (SubtitleWord schema); render mode word_by_word or sentence per subtitle_preferences
- [ ] AC-3: Subtitle text sourced from polished_script (not re-generated); alignment error <= 200ms
- [ ] AC-4: Keyword highlighting: pure code (0 LLM tokens); priority order key_data_point > percentage > number > proper_noun; SRT file exported
- [ ] AC-5: Transitions: intra-segment crossfade 0.5s, inter-chapter hard cut + chapter title card (style_lock colors, 2s display)
- [ ] AC-6: Cross-phase audit #2: subtitle text == polished_script text (diff char count = 0), storyboard shot time vs actual shot time deviation <= 0.5s, rendered data values match key_data_points, INCONSISTENCY count = 0
- [ ] AC-7: Export: H.264 encoding, bitrate and resolution matching target_platform
- [ ] AC-8: AVSyncReviewer pure L1 (0 token): AV offset <= 100ms, no blank frames (black/white pixel variance < threshold), subtitle alignment rate >= 95% (words within 200ms of audio peak), duration deviation <= 1s vs audio total, resolution matches target_platform, highlight words match key_data_points
- [ ] AC-9: Gate-P10 checks: rough_cut mp4 exists + playable + size > 0, AVSyncReviewer PASS, composition async done, no pending tasks, preferences confirmed

## Verification Commands
```bash
pytest tests/unit/pipeline/test_spec_d_008.py -v
```

## Completion Definition
RoughCutAgent with full audio mixing, subtitle pipeline (Whisper alignment + highlighting), transition effects, cross-phase audit #2, and H.264 export implemented. AVSyncReviewer is pure L1 with all 6 checks. Gate-P10 enforces all conditions. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/pipeline/test_spec_d_008.py | test_voice_0db_main_track |
| AC-1 | tests/unit/pipeline/test_spec_d_008.py | test_bgm_envelope_per_segment_type |
| AC-1 | tests/unit/pipeline/test_spec_d_008.py | test_sfx_not_exceeding_voice_minus_6db |
| AC-2 | tests/unit/pipeline/test_spec_d_008.py | test_whisper_alignment_word_level |
| AC-2 | tests/unit/pipeline/test_spec_d_008.py | test_render_mode_word_by_word |
| AC-2 | tests/unit/pipeline/test_spec_d_008.py | test_render_mode_sentence |
| AC-3 | tests/unit/pipeline/test_spec_d_008.py | test_text_from_polished_script |
| AC-3 | tests/unit/pipeline/test_spec_d_008.py | test_alignment_error_within_200ms |
| AC-4 | tests/unit/pipeline/test_spec_d_008.py | test_highlight_priority_order |
| AC-4 | tests/unit/pipeline/test_spec_d_008.py | test_no_llm_calls |
| AC-4 | tests/unit/pipeline/test_spec_d_008.py | test_srt_export |
| AC-5 | tests/unit/pipeline/test_spec_d_008.py | test_intra_segment_crossfade_05s |
| AC-5 | tests/unit/pipeline/test_spec_d_008.py | test_chapter_title_card_style_lock_2s |
| AC-6 | tests/unit/pipeline/test_spec_d_008.py | test_audit_2_subtitle_matches_script |
| AC-6 | tests/unit/pipeline/test_spec_d_008.py | test_audit_2_shot_time_deviation |
| AC-6 | tests/unit/pipeline/test_spec_d_008.py | test_audit_2_inconsistency_zero |
| AC-7 | tests/unit/pipeline/test_spec_d_008.py | test_export_h264_target_platform |
| AC-8 | tests/unit/pipeline/test_spec_d_008.py | test_av_offset_over_100ms_fail |
| AC-8 | tests/unit/pipeline/test_spec_d_008.py | test_blank_frame_detected_fail |
| AC-8 | tests/unit/pipeline/test_spec_d_008.py | test_subtitle_alignment_below_95_fail |
| AC-8 | tests/unit/pipeline/test_spec_d_008.py | test_duration_deviation_over_1s_fail |
| AC-8 | tests/unit/pipeline/test_spec_d_008.py | test_highlight_word_mismatch_fail |
| AC-8 | tests/unit/pipeline/test_spec_d_008.py | test_av_sync_reviewer_no_llm |
| AC-9 | tests/unit/pipeline/test_spec_d_008.py | test_gate_p10_pass |
| AC-9 | tests/unit/pipeline/test_spec_d_008.py | test_gate_p10_fail_unplayable |
| AC-9 | tests/unit/pipeline/test_spec_d_008.py | test_gate_p10_fail_async_running |
