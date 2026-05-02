# [SPEC-C-010] Reviewer Agent & Dual-Layer Architecture (L1 + L2)

## Metadata
- **task_id**: SPEC-C-010
- **spec_ref**: SPEC-5.2, SPEC-5.3
- **depends_on**: [SPEC-A-001, SPEC-C-001, SPEC-C-011]
- **priority**: P0
- **estimated_complexity**: L

## Scope
Implement the Reviewer Agent with fixed output format `{verdict: "PASS"|"FAIL", notes[], blocking_issues[]}` and the dual-layer review architecture. L1 is purely programmatic (0 tokens, millisecond latency). L2 is LLM-based semantic review, triggered only when L1 passes. 6 Reviewers are pure-L1 (AudioQuality, AVSync, SFX, Storyboard, Visual, Final). 6 are L1+L2 hybrid (Completeness, Structure, Style, FactChecker, MusicFit, BRollFit).

## Allowed Files
- `src/backend/agents/reviewer_agent.py`
- `src/backend/agents/reviewers/__init__.py`
- `src/backend/agents/reviewers/l1_checks.py`
- `src/backend/agents/reviewers/l2_checks.py`
- `tests/unit/backend-core/test_reviewer_agent.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**` (owned by SPEC-A)
- `src/shared/schemas/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: `verdict` only accepts `PASS` or `FAIL`, no intermediate states
- [ ] AC-2: `blocking_issues` non-empty implies `verdict=FAIL`; empty implies `verdict=PASS`
- [ ] AC-3: L1 failure prevents L2 invocation (token consumption = 0)
- [ ] AC-4: 6 pure-L1 Reviewers (AudioQuality, AVSync, SFX, Storyboard, Visual, Final) consume 0 tokens on any call
- [ ] AC-5: 6 hybrid L1+L2 Reviewers trigger L2 only after L1 passes
- [ ] AC-6: All 12 Reviewer types are registered and discoverable

## Verification Commands
```bash
pytest tests/unit/backend-core/test_spec_c_010.py -v
ruff check src/backend/agents/reviewer_agent.py src/backend/agents/reviewers/
mypy src/backend/agents/reviewer_agent.py --strict
```

## Completion Definition
Reviewer output schema enforced. Dual-layer architecture works: L1 gates L2. All 12 reviewers registered. Pure-L1 reviewers use 0 tokens. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/backend-core/test_spec_c_010.py | test_verdict_only_pass_or_fail |
| AC-2 | tests/unit/backend-core/test_spec_c_010.py | test_blocking_issues_implies_fail |
| AC-2 | tests/unit/backend-core/test_spec_c_010.py | test_empty_blocking_implies_pass |
| AC-3 | tests/unit/backend-core/test_spec_c_010.py | test_l1_fail_skips_l2 |
| AC-4 | tests/unit/backend-core/test_spec_c_010.py | test_pure_l1_zero_tokens |
| AC-5 | tests/unit/backend-core/test_spec_c_010.py | test_hybrid_l2_after_l1_pass |
| AC-6 | tests/unit/backend-core/test_spec_c_010.py | test_twelve_reviewers_registered |
