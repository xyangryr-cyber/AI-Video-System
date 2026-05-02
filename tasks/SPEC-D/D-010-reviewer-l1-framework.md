# [SPEC-D-010] L1 Programmatic Reviewer Framework

## Metadata
- **task_id**: SPEC-D-010
- **spec_ref**: SPEC-D Reviewer/Gate/Verdict unified binding, SPEC-C SPEC-5.2
- **depends_on**: [SPEC-D-001, SPEC-C-005]
- **priority**: P0
- **estimated_complexity**: M

## Scope
Implement the base framework for L1 programmatic reviewers that all phase-specific reviewers inherit from. L1 reviewers run pure code checks with 0 LLM token cost. The framework provides: base class with check registration, sequential check execution with early-stop on FAIL, verdict generation in standard format, token cost assertion (must be 0), and check result aggregation. Covers the common L1 pattern used by: CompletenessReviewer, SFXReviewer, VisualReviewer, AVSyncReviewer, FinalReviewer, and the L1 layer of MusicFitReviewer, StoryboardReviewer, BRollFitReviewer.

## Allowed Files
- `src/backend/agents/reviewers/base_reviewer.py`
- `src/backend/agents/reviewers/l1_reviewer.py`
- `tests/unit/pipeline/test_l1_reviewer_framework.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**`
- `src/shared/schemas/**`

## Acceptance Criteria
- [ ] AC-1: BaseReviewer abstract class with `review(artifact) -> Verdict` method
- [ ] AC-2: L1Reviewer subclass registers check functions via decorator or list; each check returns (pass: bool, note: str)
- [ ] AC-3: L1Reviewer executes all registered checks; aggregates results into verdict format `{verdict: PASS|FAIL, notes[], blocking_issues[]}`
- [ ] AC-4: L1Reviewer tracks token_count; asserts token_count == 0 at completion (no LLM calls allowed)
- [ ] AC-5: Failed checks populate blocking_issues with check name + failure detail
- [ ] AC-6: L1Reviewer provides `skip_l2_on_fail` flag -- when L1 fails, downstream L2 is not triggered (saves tokens)

## Verification Commands
```bash
pytest tests/unit/pipeline/test_spec_d_010.py -v
mypy src/backend/agents/reviewers/base_reviewer.py --strict
mypy src/backend/agents/reviewers/l1_reviewer.py --strict
```

## Completion Definition
BaseReviewer and L1Reviewer classes are implemented. Check registration, execution, verdict generation, and token assertion work correctly. All phase-specific L1 reviewers can inherit from this framework. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/pipeline/test_spec_d_010.py | test_base_reviewer_is_abstract |
| AC-2 | tests/unit/pipeline/test_spec_d_010.py | test_register_checks |
| AC-3 | tests/unit/pipeline/test_spec_d_010.py | test_all_pass_verdict |
| AC-3 | tests/unit/pipeline/test_spec_d_010.py | test_fail_verdict_with_blocking_issues |
| AC-4 | tests/unit/pipeline/test_spec_d_010.py | test_token_count_zero |
| AC-5 | tests/unit/pipeline/test_spec_d_010.py | test_failed_check_in_blocking_issues |
| AC-6 | tests/unit/pipeline/test_spec_d_010.py | test_skip_l2_on_l1_fail |
