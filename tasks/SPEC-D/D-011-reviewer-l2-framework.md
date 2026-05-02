# [SPEC-D-011] L2 LLM Reviewer Framework

## Metadata
- **task_id**: SPEC-D-011
- **spec_ref**: SPEC-D Reviewer/Gate/Verdict unified binding, SPEC-C SPEC-5.2
- **depends_on**: [SPEC-D-010]
- **priority**: P1
- **estimated_complexity**: M

## Scope
Implement the base framework for L2 LLM-based reviewers. L2 reviewers run semantic/qualitative checks using LLM calls, only triggered after L1 checks all pass (to avoid wasting tokens). The framework provides: L2Reviewer base class inheriting from BaseReviewer, conditional trigger (only after L1 PASS), LLM call wrapper with token tracking, structured output parsing via Instructor, verdict merging (L1 + L2 results), and cost logging. Used by the L2 layer of: FactChecker, MusicFitReviewer, StoryboardReviewer, BRollFitReviewer, and ViewerExperienceReviewer.

## Allowed Files
- `src/backend/agents/reviewers/l2_reviewer.py`
- `src/backend/agents/reviewers/dual_layer_reviewer.py`
- `tests/unit/pipeline/test_l2_reviewer_framework.py`
- `tests/unit/pipeline/test_dual_layer_reviewer.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**`
- `src/shared/schemas/**`

## Acceptance Criteria
- [ ] AC-1: L2Reviewer base class with `review_semantic(artifact) -> Verdict` method; tracks input/output token counts
- [ ] AC-2: L2Reviewer uses Instructor for structured LLM output parsing into verdict format
- [ ] AC-3: DualLayerReviewer composes L1Reviewer + L2Reviewer; L2 only runs when L1 verdict=PASS
- [ ] AC-4: When L1 fails, DualLayerReviewer returns L1 verdict immediately with l2_skipped=true and l2_token_cost=0
- [ ] AC-5: When L1+L2 both run, verdict merges blocking_issues from both layers
- [ ] AC-6: Token usage and cost logged per review call (agent_name, input_tokens, output_tokens, cost_usd)

## Verification Commands
```bash
pytest tests/unit/pipeline/test_spec_d_011.py -v
mypy src/backend/agents/reviewers/l2_reviewer.py --strict
mypy src/backend/agents/reviewers/dual_layer_reviewer.py --strict
```

## Completion Definition
L2Reviewer and DualLayerReviewer classes are implemented. Conditional L2 execution verified (L1 fail -> L2 skipped, 0 tokens). Token tracking and cost logging work. All phase-specific dual-layer reviewers can compose using this framework. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/pipeline/test_spec_d_011.py | test_l2_reviewer_tracks_tokens |
| AC-2 | tests/unit/pipeline/test_spec_d_011.py | test_instructor_structured_output |
| AC-3 | tests/unit/pipeline/test_spec_d_011.py | test_l2_runs_only_after_l1_pass |
| AC-4 | tests/unit/pipeline/test_spec_d_011.py | test_l1_fail_skips_l2_zero_tokens |
| AC-5 | tests/unit/pipeline/test_spec_d_011.py | test_merged_verdict_both_layers |
| AC-6 | tests/unit/pipeline/test_spec_d_011.py | test_token_cost_logged |
