# [SPEC-D-016] ViewerExperienceReviewer (SPEC-9.13)

## Metadata
- **task_id**: SPEC-D-016
- **spec_ref**: SPEC-9.13
- **depends_on**: [SPEC-D-008, SPEC-D-011]
- **priority**: P1
- **estimated_complexity**: M

## Scope
Implement the ViewerExperienceReviewer, a v3.15 addition that evaluates rough cut video (P10) from a human viewer perspective. This is a pure L2 LLM reviewer that assesses 6 dimensions: hook appeal (first 15s), pacing (scene switch frequency + info density), information density (data points per minute <= 3), emotional arc (against narrative template), ending impact (last 15s), and overall watchability (1-10 score, >= 6 to pass). Triggered automatically after AVSyncReviewer PASS. Verdict=FAIL does not block Gate-P10 but shows warning in frontend and passes improvement_suggestions to P11 FinalCutAgent.

## Allowed Files
- `src/backend/agents/reviewers/viewer_experience_reviewer.py`
- `tests/unit/pipeline/test_viewer_experience_reviewer.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**`
- `src/shared/schemas/**`

## Acceptance Criteria
- [ ] AC-1: Auto-triggered after P10 AVSyncReviewer PASS; added to task_ledger as additional check
- [ ] AC-2: Takes 4 inputs: P10 rough_cut structural metadata (shot timeline + types + emotion labels), P3 polished_script full text, P5 emotion_curve.json, timeline.json
- [ ] AC-3: Evaluates 6 dimensions with specific PASS/FAIL criteria: hook_appeal (curiosity/suspense/empathy within 5s), pacing (no >30s monotone, no >20s high-density bombardment), information_density (<= 3 new concepts/data points per minute), emotional_arc (clear climax, not flat), ending_impact (clear CTA or golden quote), overall score (1-10)
- [ ] AC-4: Output format: verdict, overall_score (1-10), dimension_scores (5 dimensions), improvement_suggestions[] (each with time_range/dimension/issue/suggestion), notes[], blocking_issues[]
- [ ] AC-5: overall_score < 6 -> verdict=FAIL
- [ ] AC-6: verdict=FAIL does NOT block Gate-P10; frontend displays warning icon; improvement_suggestions passed to P11 FinalCutAgent input context
- [ ] AC-7: improvement_suggestions are advisory input for P11 (not mandatory execution)

## Verification Commands
```bash
pytest tests/unit/pipeline/test_spec_d_016.py -v
mypy src/backend/agents/reviewers/viewer_experience_reviewer.py --strict
```

## Completion Definition
ViewerExperienceReviewer implemented with all 6 evaluation dimensions. Auto-trigger after AVSyncReviewer PASS verified. Non-blocking FAIL behavior verified. Output format with improvement_suggestions correct. P11 integration point defined. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/pipeline/test_spec_d_016.py | test_auto_trigger_after_av_sync_pass |
| AC-2 | tests/unit/pipeline/test_spec_d_016.py | test_requires_4_inputs |
| AC-3 | tests/unit/pipeline/test_spec_d_016.py | test_evaluates_hook_appeal |
| AC-3 | tests/unit/pipeline/test_spec_d_016.py | test_evaluates_pacing_monotone |
| AC-3 | tests/unit/pipeline/test_spec_d_016.py | test_evaluates_information_density |
| AC-3 | tests/unit/pipeline/test_spec_d_016.py | test_evaluates_emotional_arc |
| AC-3 | tests/unit/pipeline/test_spec_d_016.py | test_evaluates_ending_impact |
| AC-4 | tests/unit/pipeline/test_spec_d_016.py | test_output_format_complete |
| AC-4 | tests/unit/pipeline/test_spec_d_016.py | test_improvement_suggestion_fields |
| AC-5 | tests/unit/pipeline/test_spec_d_016.py | test_score_below_6_verdict_fail |
| AC-5 | tests/unit/pipeline/test_spec_d_016.py | test_score_6_or_above_verdict_pass |
| AC-6 | tests/unit/pipeline/test_spec_d_016.py | test_fail_does_not_block_gate_p10 |
| AC-6 | tests/unit/pipeline/test_spec_d_016.py | test_suggestions_passed_to_p11 |
| AC-7 | tests/unit/pipeline/test_spec_d_016.py | test_suggestions_advisory_not_mandatory |
