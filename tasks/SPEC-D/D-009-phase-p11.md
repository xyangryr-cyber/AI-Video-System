# [SPEC-D-009] Phase P11: FinalCut Producer, FinalReviewer, Gate

## Metadata
- **task_id**: SPEC-D-009
- **spec_ref**: SPEC-9.11 (P11)
- **depends_on**: [SPEC-D-008]
- **priority**: P0
- **estimated_complexity**: L
- **bdd_tags**: [@phase11]

## Scope
Implement P11 FinalCutAgent (async), FinalReviewer, and Gate-P11. FinalCutAgent handles final adjustments (shot replacement, volume tuning, subtitle fixes, transition tweaks, intro/outro params), generates 9 cover images (3 templates x 3 sizes), multi-platform adaptation via PLATFORM_PROFILES, and brand_kit overlay (intro/outro/watermark/logo). FinalReviewer is pure L1 (0 token) performing 8 quality checks + cross-phase audit #3 (summary of all prior audits). Gate-P11 marks project as completed on pass.

## Allowed Files
- `src/backend/agents/final_cut_agent.py`
- `src/backend/agents/reviewers/final_reviewer.py`
- `src/backend/engine/gates/gate_p11.py`
- `src/backend/services/cover_generator.py`
- `src/backend/services/brand_kit_overlay.py`
- `src/backend/services/platform_profiles.py`
- `tests/unit/pipeline/test_final_cut_agent.py`
- `tests/unit/pipeline/test_final_reviewer.py`
- `tests/unit/pipeline/test_gate_p11.py`
- `tests/unit/pipeline/test_cover_generator.py`
- `tests/unit/pipeline/test_brand_kit_overlay.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**`
- `src/shared/schemas/**`

## Acceptance Criteria
- [ ] AC-1: FinalCutAgent supports adjustments: shot replacement, volume tuning (+/-3dB), subtitle correction, transition adjustment, intro/outro parameter modification
- [ ] AC-2: Cover generation: 3 templates (data_focus with key_data_point number, chart_preview with chart screenshot, clean_text with brand color background) x 3 sizes (16:9=1280x720, 3:4=900x1200, 1:1=1080x1080) = 9 files via Pillow
- [ ] AC-3: data_focus cover's large number sourced from key_data_points
- [ ] AC-4: Multi-platform: PLATFORM_PROFILES mapping (platform -> resolution/bitrate/format/cover_size); V1 only 16:9 horizontal; target_platform=douyin -> explicit deferral message "vertical format in V1.5"
- [ ] AC-5: brand_kit overlay: intro Remotion Sequence prepended (duration = brand_kit.intro_template.duration, default 3s), outro appended (duration = brand_kit.outro_template.duration, default 3s), watermark AbsoluteFill at brand_kit position/opacity (opacity=0 -> not rendered), logo AbsoluteFill at brand_kit position/opacity; brand_kit from API not file
- [ ] AC-6: Export: H.264 per platform per PLATFORM_PROFILES bitrate/resolution; each target_platform has output file
- [ ] AC-7: FinalReviewer pure L1 (0 token), 8 checks: AV offset <= 50ms, video completeness (intro/body/outro present), audio completeness (BGM/SFX/voice if not skipped), subtitle coverage, resolution per platform, cover quality (correct sizes + >=3 templates), all files playable, export failure count = 0
- [ ] AC-8: FinalReviewer cross-phase audit #3: collects all INCONSISTENCY from audit #1 (P7) and #2 (P10); every record must be resolved or accepted_deviation; unresolved -> FAIL
- [ ] AC-9: Export failure retry: max 2 auto-retries; after 2 failures stop auto-retry, show manual retry button + failure details (error code + stack summary)
- [ ] AC-10: Gate-P11 checks: all platform mp4 files exist + playable, cover files exist, subtitle files exist, FinalReviewer PASS, export async done, no pending tasks, preferences confirmed; on PASS -> project.status="completed", project.completed_at=now(), frontend read-only mode

## Verification Commands
```bash
pytest tests/unit/pipeline/test_spec_d_009.py -v
```

## Completion Definition
FinalCutAgent with all adjustment capabilities, cover generation, platform adaptation, and brand_kit overlay implemented. FinalReviewer performs all 8 checks + audit #3 as pure L1. Gate-P11 sets project completion state on pass. Export retry logic implemented. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/pipeline/test_spec_d_009.py | test_shot_replacement |
| AC-1 | tests/unit/pipeline/test_spec_d_009.py | test_volume_tuning_3db |
| AC-2 | tests/unit/pipeline/test_spec_d_009.py | test_generates_9_covers |
| AC-2 | tests/unit/pipeline/test_spec_d_009.py | test_cover_sizes_correct |
| AC-3 | tests/unit/pipeline/test_spec_d_009.py | test_data_focus_number_from_key_data_point |
| AC-4 | tests/unit/pipeline/test_spec_d_009.py | test_platform_profiles_mapping |
| AC-4 | tests/unit/pipeline/test_spec_d_009.py | test_douyin_deferral_message |
| AC-5 | tests/unit/pipeline/test_spec_d_009.py | test_intro_prepended_correct_duration |
| AC-5 | tests/unit/pipeline/test_spec_d_009.py | test_outro_appended_correct_duration |
| AC-5 | tests/unit/pipeline/test_spec_d_009.py | test_watermark_opacity_zero_not_rendered |
| AC-5 | tests/unit/pipeline/test_spec_d_009.py | test_brand_kit_from_api_not_file |
| AC-6 | tests/unit/pipeline/test_spec_d_009.py | test_export_per_platform |
| AC-7 | tests/unit/pipeline/test_spec_d_009.py | test_av_offset_over_50ms_fail |
| AC-7 | tests/unit/pipeline/test_spec_d_009.py | test_missing_intro_fail |
| AC-7 | tests/unit/pipeline/test_spec_d_009.py | test_subtitle_incomplete_fail |
| AC-7 | tests/unit/pipeline/test_spec_d_009.py | test_cover_wrong_size_fail |
| AC-7 | tests/unit/pipeline/test_spec_d_009.py | test_export_failure_count_nonzero_fail |
| AC-7 | tests/unit/pipeline/test_spec_d_009.py | test_final_reviewer_no_llm |
| AC-8 | tests/unit/pipeline/test_spec_d_009.py | test_audit_3_unresolved_inconsistency_fail |
| AC-8 | tests/unit/pipeline/test_spec_d_009.py | test_audit_3_all_resolved_pass |
| AC-9 | tests/unit/pipeline/test_spec_d_009.py | test_export_retry_max_2 |
| AC-9 | tests/unit/pipeline/test_spec_d_009.py | test_export_retry_stop_after_2_failures |
| AC-10 | tests/unit/pipeline/test_spec_d_009.py | test_gate_p11_pass_sets_completed |
| AC-10 | tests/unit/pipeline/test_spec_d_009.py | test_gate_p11_fail_missing_cover |
| AC-10 | tests/unit/pipeline/test_spec_d_009.py | test_gate_p11_fail_async_running |
