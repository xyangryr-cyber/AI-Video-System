# [SPEC-E-007] Artifact 3-State Status Badge

## Metadata
- **task_id**: SPEC-E-007
- **spec_ref**: SPEC-2.4
- **depends_on**: [SPEC-A-001, SPEC-E-003]
- **priority**: P1
- **estimated_complexity**: S

## Scope
Implement an ArtifactStatusBadge component that renders a visual badge for artifact health status: `ok` (default/hidden or green), `damaged` (red badge), `missing` (red badge). The badge is displayed on phase navigation items and preview components. Status is read from ProjectState (`phases[].artifact_status`) and updates via periodic polling or WebSocket events when the backend artifact scanner detects changes (10-minute scan interval).

## Allowed Files
- `src/frontend/components/ArtifactStatusBadge.tsx`
- `src/frontend/hooks/useArtifactStatus.ts`
- `tests/unit/frontend/ArtifactStatusBadge.test.tsx`

## Forbidden Files
- `src/backend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: Badge renders nothing (or green) for `artifact_status=ok`
- [ ] AC-2: Badge renders red with "damaged" label/tooltip for `artifact_status=damaged`
- [ ] AC-3: Badge renders red with "missing" label/tooltip for `artifact_status=missing`
- [ ] AC-4: Badge is integrated into phase navigation items
- [ ] AC-5: Badge updates when ProjectState refreshes (via state recovery or WebSocket)

## Verification Commands
```bash
pytest tests/unit/frontend/test_spec_e_007.py -v
tsc --noEmit
```

## Completion Definition
Artifact status badge visually distinguishes ok/damaged/missing states with correct colors and labels. Integrated into phase navigation. Updates reactively. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/frontend/test_spec_e_007.py | test_ok_status_hidden_or_green |
| AC-2 | tests/unit/frontend/test_spec_e_007.py | test_damaged_shows_red_badge |
| AC-3 | tests/unit/frontend/test_spec_e_007.py | test_missing_shows_red_badge |
| AC-4 | tests/unit/frontend/test_spec_e_007.py | test_integrated_in_phase_nav |
| AC-5 | tests/unit/frontend/test_spec_e_007.py | test_updates_on_state_refresh |
