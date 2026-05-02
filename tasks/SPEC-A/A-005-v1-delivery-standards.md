# [SPEC-A-005] V1 Delivery Standards & Design Principles

## Metadata
- **task_id**: SPEC-A-005
- **spec_ref**: SPEC-0.1, SPEC-0.2, SPEC-0.3
- **depends_on**: []
- **priority**: P1
- **estimated_complexity**: S
- **bdd_tags**: [@performance]

## Scope
Codify the V1 quantitative delivery standards (SPEC-0.1), V1.5 kill-switch triggers (SPEC-0.2), and P1-P7 design principle checklist (SPEC-0.3) as machine-readable constants and a PR review checklist. Includes SQL query templates for the V1.5 usage metrics.

## Allowed Files
- `src/shared/constants/delivery_standards.py`
- `src/shared/constants/delivery_standards.ts`
- `docs/review_checklist.md`
- `scripts/v15_metrics.sql`
- `tests/unit/contracts/test_delivery_standards.py`

## Forbidden Files
- `src/backend/api/**`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1: Delivery standard constants defined: success_rate≥0.9, p50_time≤45min, p90_time≤60min, p50_cost≤$8, p90_cost≤$15, first_frame_load≤3s, router_accuracy≥0.85, router_p95≤3s
- [ ] AC-2: V1.5 kill-switch thresholds defined: inject_subtask_usage<0.3, preference_extractor_acceptance<0.2, sample_size=20
- [ ] AC-3: `docs/review_checklist.md` lists P1-P7 as explicit check items
- [ ] AC-4: SQL script `scripts/v15_metrics.sql` produces inject_subtask usage rate and preference acceptance rate from events table
- [ ] AC-5: No code pattern `self.history.append` allowed (P5 stateless agent principle)
- [ ] AC-6: Constants assert SQLite is the only structured state write target (P4)

## Verification Commands
```bash
pytest tests/unit/contracts/test_spec_a_005.py -v
sqlite3 :memory: < scripts/v15_metrics.sql  # syntax check
```

## Completion Definition
Constants files exist with all V1 thresholds. Review checklist file contains P1-P7. SQL script is syntactically valid. Tests verify constant values match spec.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/contracts/test_spec_a_005.py | test_v1_delivery_thresholds |
| AC-2 | tests/unit/contracts/test_spec_a_005.py | test_v15_killswitch_thresholds |
| AC-3 | tests/unit/contracts/test_spec_a_005.py | test_review_checklist_contains_p1_p7 |
| AC-4 | tests/unit/contracts/test_spec_a_005.py | test_v15_metrics_sql_syntax |
| AC-5 | tests/unit/contracts/test_spec_a_005.py | test_no_stateful_agent_pattern |
| AC-6 | tests/unit/contracts/test_spec_a_005.py | test_sqlite_single_state_target |
