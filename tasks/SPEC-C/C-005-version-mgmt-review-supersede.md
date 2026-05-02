# [SPEC-C-005] Version Management & Review Supersede

## Metadata
- **task_id**: SPEC-C-005
- **spec_ref**: SPEC-3.5
- **depends_on**: [SPEC-A-001, SPEC-C-001, SPEC-C-002]
- **priority**: P0
- **estimated_complexity**: M

## Scope
Implement artifact versioning: when `generate_artifact` or `user_revision` completes, increment `phases.artifact_version`, auto-append a new review task targeting the new version, and mark any older pending/queued review tasks as `superseded`. Guarantee no two pending reviews target different versions within the same phase.

## Allowed Files
- `src/backend/engine/workflow_engine.py`
- `src/backend/engine/version_manager.py`
- `tests/unit/backend-core/test_version_manager.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**` (owned by SPEC-A)
- `src/shared/schemas/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: `generate_artifact` completion increments `phases.artifact_version` by 1
- [ ] AC-2: `user_revision` completion increments `phases.artifact_version` by 1
- [ ] AC-3: After version increment, a new review task is auto-created with `target_version` = new version
- [ ] AC-4: Older pending/queued review tasks are set to `superseded`
- [ ] AC-5: No two pending review tasks exist for different versions in the same phase
- [ ] AC-6: Superseded tasks are not picked up by Dispatcher

## Verification Commands
```bash
pytest tests/unit/backend-core/test_spec_c_005.py -v
ruff check src/backend/engine/version_manager.py
mypy src/backend/engine/version_manager.py --strict
```

## Completion Definition
Version auto-increment works on artifact generation and user revision. Review tasks are auto-created and old ones superseded atomically. Invariant enforced: at most one pending review per phase. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/backend-core/test_spec_c_005.py | test_generate_artifact_increments_version |
| AC-2 | tests/unit/backend-core/test_spec_c_005.py | test_user_revision_increments_version |
| AC-3 | tests/unit/backend-core/test_spec_c_005.py | test_auto_create_review_for_new_version |
| AC-4 | tests/unit/backend-core/test_spec_c_005.py | test_old_reviews_superseded |
| AC-5 | tests/unit/backend-core/test_spec_c_005.py | test_no_duplicate_pending_reviews |
| AC-6 | tests/unit/backend-core/test_spec_c_005.py | test_superseded_not_dispatched |
