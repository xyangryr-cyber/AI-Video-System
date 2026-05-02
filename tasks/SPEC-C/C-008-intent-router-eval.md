# [SPEC-C-008] IntentRouter Accuracy Eval Test Set

## Metadata
- **task_id**: SPEC-C-008
- **spec_ref**: SPEC-4.7
- **depends_on**: [SPEC-C-006, SPEC-C-007]
- **priority**: P1
- **estimated_complexity**: M

## Scope
Create a 100-entry labeled test set (`tests/eval/router.jsonl`) covering all Router action types with >=10 examples per action type. Build an evaluation script that runs the Router against all entries and reports overall accuracy (must >=85%) and per-action-type accuracy (must >=70% each).

## Allowed Files
- `tests/eval/router.jsonl`
- `tests/eval/eval_router.py`
- `tests/eval/conftest.py`

## Forbidden Files
- `src/frontend/**`
- `src/backend/engine/**`
- `src/shared/**`

## Acceptance Criteria
- [ ] AC-1: `tests/eval/router.jsonl` exists with exactly 100 labeled entries
- [ ] AC-2: Each action type has >=10 entries in the test set
- [ ] AC-3: Eval script produces overall accuracy metric
- [ ] AC-4: Overall accuracy >=85% when run against live Router
- [ ] AC-5: Per-action-type accuracy >=70% for every type

## Verification Commands
```bash
pytest tests/unit/backend-core/test_spec_c_008.py -v
python tests/eval/eval_router.py --report
wc -l tests/eval/router.jsonl  # should output 100
```

## Completion Definition
100-entry JSONL test set exists with balanced coverage. Eval script runs and reports accuracy metrics. Accuracy thresholds met. No action type falls below 70%.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/backend-core/test_spec_c_008.py | test_jsonl_has_100_entries |
| AC-2 | tests/unit/backend-core/test_spec_c_008.py | test_each_action_type_min_10 |
| AC-3 | tests/unit/backend-core/test_spec_c_008.py | test_eval_produces_accuracy |
| AC-4 | tests/unit/backend-core/test_spec_c_008.py | test_overall_accuracy_ge_85 |
| AC-5 | tests/unit/backend-core/test_spec_c_008.py | test_per_action_accuracy_ge_70 |
