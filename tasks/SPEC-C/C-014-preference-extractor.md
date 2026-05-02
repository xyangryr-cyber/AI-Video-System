# [SPEC-C-014] PreferenceExtractor, Confirmation & Three-Level Persistence

## Metadata
- **task_id**: SPEC-C-014
- **spec_ref**: SPEC-7.1, SPEC-7.2, SPEC-7.3, SPEC-7.4
- **depends_on**: [SPEC-A-001, SPEC-C-004, SPEC-C-011]
- **priority**: P1
- **estimated_complexity**: L
- **bdd_tags**: [@preferences, @preferences-2]

## Scope
Implement PreferenceExtractor triggered on `POST /projects/{id}/advance`: extracts candidate preferences with confidence, evidence, scope_suggestion, and conflicts_with. Filter out candidates with confidence <0.6. Parse via Instructor (no hand-written JSON parsing). Handle `nothing_found=true` (user must still click "skip"). Implement user confirmation flow (accept/reject/edit/scope). Three-level persistence: global_rules_md, user_preferences_md, project_preferences_md. New projects inherit global+user, project starts empty. Snapshot versioning: keep last 20 snapshots, support rollback (rollback creates a new version and writes `preference.rollback` event).

## Allowed Files
- `src/backend/agents/preference_extractor.py`
- `src/backend/services/preference_service.py`
- `tests/unit/backend-core/test_preference_extractor.py`
- `tests/unit/backend-core/test_preference_service.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**` (owned by SPEC-A)
- `src/shared/schemas/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: Extracted candidates have non-empty `evidence` and `confidence >= 0.6`
- [ ] AC-2: `nothing_found=true` still requires user interaction (no auto-skip)
- [ ] AC-3: Extraction uses Instructor, no hand-written JSON parsing
- [ ] AC-4: Accept writes rule to `preferences` table with correct scope
- [ ] AC-5: Edit uses modified text, original text is NOT persisted
- [ ] AC-6: Confirmation updates `preferences_confirmed_at`
- [ ] AC-7: New project has empty `project_preferences_md`, inherits global+user
- [ ] AC-8: `snapshot.md` refresh timestamp matches `preferences_confirmed_at`
- [ ] AC-9: Snapshots beyond 20 trigger deletion of the oldest
- [ ] AC-10: Rollback creates a new version record (not an in-place revert)
- [ ] AC-11: Rollback writes `preference.rollback` event to `events` table

## Verification Commands
```bash
pytest tests/unit/backend-core/test_spec_c_014.py -v
ruff check src/backend/agents/preference_extractor.py src/backend/services/preference_service.py
mypy src/backend/agents/preference_extractor.py src/backend/services/preference_service.py --strict
```

## Completion Definition
PreferenceExtractor extracts and filters candidates. User confirmation flow works with accept/reject/edit. Three-level persistence with correct inheritance. Snapshot versioning with rollback and event logging. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/backend-core/test_spec_c_014.py | test_candidates_confidence_ge_06 |
| AC-2 | tests/unit/backend-core/test_spec_c_014.py | test_nothing_found_requires_user |
| AC-3 | tests/unit/backend-core/test_spec_c_014.py | test_uses_instructor_not_manual_parse |
| AC-4 | tests/unit/backend-core/test_spec_c_014.py | test_accept_writes_correct_scope |
| AC-5 | tests/unit/backend-core/test_spec_c_014.py | test_edit_uses_modified_text |
| AC-6 | tests/unit/backend-core/test_spec_c_014.py | test_confirm_updates_timestamp |
| AC-7 | tests/unit/backend-core/test_spec_c_014.py | test_new_project_empty_project_prefs |
| AC-8 | tests/unit/backend-core/test_spec_c_014.py | test_snapshot_refresh_matches_confirmed |
| AC-9 | tests/unit/backend-core/test_spec_c_014.py | test_snapshot_cap_at_20 |
| AC-10 | tests/unit/backend-core/test_spec_c_014.py | test_rollback_creates_new_version |
| AC-11 | tests/unit/backend-core/test_spec_c_014.py | test_rollback_writes_event |
