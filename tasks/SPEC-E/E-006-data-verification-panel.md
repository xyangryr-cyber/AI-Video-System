# [SPEC-E-006] Data Verification Panel

## Metadata
- **task_id**: SPEC-E-006
- **spec_ref**: SPEC-2.7
- **depends_on**: [SPEC-A-001, SPEC-E-003]
- **priority**: P1
- **estimated_complexity**: L

## Scope
Implement the DataVerificationPanel component for the workflow page sidebar. Displays all `key_data_points` with their verification status (verified/pending/failed/stale) using color-coded icons. Includes summary stats bar, interactive buttons ([Verify] triggers `inject_subtask(verify)`, [Manual Confirm] sets trust_level to user_verified), expandable fact-checker notes, and real-time updates via WebSocket. Data sourced from review tasks (type=review, reviewer=fact_checker) and phase artifact key_data_points.

## Allowed Files
- `src/frontend/components/DataVerificationPanel.tsx`
- `src/frontend/components/DataPointRow.tsx`
- `src/frontend/hooks/useDataVerification.ts`
- `src/frontend/types/dataVerification.ts`
- `tests/unit/frontend/DataVerificationPanel.test.tsx`
- `tests/unit/frontend/DataPointRow.test.tsx`

## Forbidden Files
- `src/backend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: Panel displays summary stats bar: total count, verified (green), pending (yellow), failed (red), stale (gray)
- [ ] AC-2: Each data point row shows icon, value, source, trust_level, and verification timestamp
- [ ] AC-3: `trust_level=llm_generated` rows display yellow icon and [Verify] + [Manual Confirm] buttons
- [ ] AC-4: `trust_level=stale` rows display gray icon and [Verify] button (re-verify)
- [ ] AC-5: Clicking [Verify] triggers subtask injection via API call
- [ ] AC-6: Clicking [Manual Confirm] updates trust_level to `user_verified` and row turns green
- [ ] AC-7: Clicking a row expands to show FactChecker notes
- [ ] AC-8: FactChecker returning `verdict=refuted` renders the row in red
- [ ] AC-9: Summary stats update in real-time via WebSocket events
- [ ] AC-10: Stats numbers are consistent with actual row states at all times

## Verification Commands
```bash
pytest tests/unit/frontend/test_spec_e_006.py -v
tsc --noEmit
```

## Completion Definition
Data verification panel renders all data points with correct status icons, buttons trigger correct API calls, expandable notes work, real-time stats update via WebSocket. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/frontend/test_spec_e_006.py | test_summary_stats_bar |
| AC-2 | tests/unit/frontend/test_spec_e_006.py | test_renders_data_point_fields |
| AC-3 | tests/unit/frontend/test_spec_e_006.py | test_llm_generated_shows_verify_and_confirm |
| AC-4 | tests/unit/frontend/test_spec_e_006.py | test_stale_shows_reverify |
| AC-5 | tests/unit/frontend/test_spec_e_006.py | test_verify_triggers_subtask |
| AC-6 | tests/unit/frontend/test_spec_e_006.py | test_manual_confirm_updates_trust |
| AC-7 | tests/unit/frontend/test_spec_e_006.py | test_expand_shows_notes |
| AC-8 | tests/unit/frontend/test_spec_e_006.py | test_refuted_renders_red |
| AC-9 | tests/unit/frontend/test_spec_e_006.py | test_ws_realtime_stats_update |
| AC-10 | tests/unit/frontend/test_spec_e_006.py | test_stats_consistent_with_rows |
