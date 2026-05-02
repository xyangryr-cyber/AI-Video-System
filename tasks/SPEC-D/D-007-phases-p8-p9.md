# [SPEC-D-007] Phase P8-P9: Keyframe Render & B-Roll Producers, Reviewers, Gates

## Metadata
- **task_id**: SPEC-D-007
- **spec_ref**: SPEC-9.8 (P8), SPEC-9.9 (P9)
- **depends_on**: [SPEC-D-006]
- **priority**: P1
- **estimated_complexity**: L
- **bdd_tags**: [@phase8]

## Scope
Implement P8 (KeyframeRenderAgent async + VisualReviewer + Gate-P8) and P9 (BRollAgent + BRollFitReviewer + Gate-P9). P8 renders all template-type shots via three-layer architecture (ECharts + React + Remotion), performs oral-visual number cross-check, chart data provenance audit, and handles degradation (failed shots -> default text card). P9 handles B-Roll sourcing with semantic relevance scoring, quality filtering, style_lock color matching, and 3-level fallback. VisualReviewer is pure L1. BRollFitReviewer is L1+L2.

## Allowed Files
- `src/backend/agents/keyframe_render_agent.py`
- `src/backend/agents/broll_agent.py`
- `src/backend/agents/reviewers/visual_reviewer.py`
- `src/backend/agents/reviewers/broll_fit_reviewer.py`
- `src/backend/engine/gates/gate_p8.py`
- `src/backend/engine/gates/gate_p9.py`
- `src/backend/services/render_engine_selector.py`
- `tests/unit/pipeline/test_keyframe_render_agent.py`
- `tests/unit/pipeline/test_broll_agent.py`
- `tests/unit/pipeline/test_visual_reviewer.py`
- `tests/unit/pipeline/test_broll_fit_reviewer.py`
- `tests/unit/pipeline/test_gate_p8.py`
- `tests/unit/pipeline/test_gate_p9.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**`
- `src/shared/schemas/**`

## Acceptance Criteria
- [ ] AC-1: KeyframeRenderAgent renders all template-type shots; render engine selection by template_type (chart animation -> Remotion+ECharts, info cards -> Remotion+React, static -> Pillow)
- [ ] AC-2: Oral-visual number cross-check: every shot's numeric values match polished_script key_data_points value/unit exactly; mismatch count = 0
- [ ] AC-3: Chart data provenance audit: every chart data value traceable via data_point_id to P2 key_data_points; audit logged in render_results.json
- [ ] AC-4: Color consistency: all renders read color params from style_lock.json; no hardcoded colors
- [ ] AC-5: Degradation: failed shots replaced with default text card (style_lock.background color, shot title + narration_text summary, is_downgraded=true)
- [ ] AC-6: Render success rate >= 90% required
- [ ] AC-7: VisualReviewer pure L1 (0 token): success rate >= 90%, file existence + size > 0, color palette RGB diff <= 30/channel vs style_lock, resolution matches target_platform, data value correctness
- [ ] AC-8: Gate-P8 checks: render_results.json exists + success >= 90%, VisualReviewer PASS, render async done, no pending tasks, preferences confirmed
- [ ] AC-9: BRollAgent assigns B-Roll to broll-type shots; semantic relevance score >= 0.7 required; quality filter (>=720p, no watermark, 16:9 aspect)
- [ ] AC-10: BRoll visual_style filtering based on style_lock color tone (warm/cool/high-contrast)
- [ ] AC-11: BRoll 3-level fallback: Pexels -> Pixabay -> Placeholder(Pillow+description, is_placeholder=true); SDK calls logged; fallback logged
- [ ] AC-12: BRollFitReviewer L1 (0 token): resolution >= target, duration >= shot need, copyright valid, no copyright_blocked, coverage >= 30% (low coverage = downgrade not block); L2 (LLM, after L1 pass): semantic relevance
- [ ] AC-13: Gate-P9 checks: broll_assignments JSON + files exist, BRollFitReviewer PASS (coverage downgrade does not block), no pending tasks, preferences confirmed

## Verification Commands
```bash
pytest tests/unit/pipeline/test_spec_d_007.py -v
```

## Completion Definition
KeyframeRenderAgent with 3-layer engine selection, cross-check, provenance audit, and degradation implemented. BRollAgent with semantic scoring, quality filter, style matching, and 3-level fallback implemented. Both reviewers enforce all checks. Gates handle async completion and degradation scenarios. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/pipeline/test_spec_d_007.py | test_render_engine_selection_by_template_type |
| AC-2 | tests/unit/pipeline/test_spec_d_007.py | test_oral_visual_number_cross_check |
| AC-3 | tests/unit/pipeline/test_spec_d_007.py | test_chart_data_provenance_audit |
| AC-4 | tests/unit/pipeline/test_spec_d_007.py | test_color_from_style_lock_no_hardcode |
| AC-5 | tests/unit/pipeline/test_spec_d_007.py | test_degradation_text_card |
| AC-6 | tests/unit/pipeline/test_spec_d_007.py | test_success_rate_threshold |
| AC-7 | tests/unit/pipeline/test_spec_d_007.py | test_visual_reviewer_pure_l1 |
| AC-7 | tests/unit/pipeline/test_spec_d_007.py | test_success_rate_below_90_fail |
| AC-7 | tests/unit/pipeline/test_spec_d_007.py | test_color_palette_deviation_fail |
| AC-7 | tests/unit/pipeline/test_spec_d_007.py | test_resolution_mismatch_fail |
| AC-8 | tests/unit/pipeline/test_spec_d_007.py | test_gate_p8_pass |
| AC-8 | tests/unit/pipeline/test_spec_d_007.py | test_gate_p8_fail_low_success_rate |
| AC-8 | tests/unit/pipeline/test_spec_d_007.py | test_gate_p8_fail_async_running |
| AC-9 | tests/unit/pipeline/test_spec_d_007.py | test_semantic_relevance_threshold |
| AC-9 | tests/unit/pipeline/test_spec_d_007.py | test_quality_filter_720p_no_watermark |
| AC-10 | tests/unit/pipeline/test_spec_d_007.py | test_visual_style_from_style_lock |
| AC-11 | tests/unit/pipeline/test_spec_d_007.py | test_fallback_pexels_to_pixabay |
| AC-11 | tests/unit/pipeline/test_spec_d_007.py | test_fallback_to_placeholder |
| AC-12 | tests/unit/pipeline/test_spec_d_007.py | test_l1_resolution_fail |
| AC-12 | tests/unit/pipeline/test_spec_d_007.py | test_l1_copyright_blocked_fail |
| AC-12 | tests/unit/pipeline/test_spec_d_007.py | test_coverage_below_30_downgrade_not_block |
| AC-12 | tests/unit/pipeline/test_spec_d_007.py | test_l1_fail_skips_l2 |
| AC-13 | tests/unit/pipeline/test_spec_d_007.py | test_gate_p9_pass |
| AC-13 | tests/unit/pipeline/test_spec_d_007.py | test_gate_p9_coverage_downgrade_still_pass |
