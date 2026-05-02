# [SPEC-E-004] Settings Page

## Metadata
- **task_id**: SPEC-E-004
- **spec_ref**: SPEC-2.5
- **depends_on**: [SPEC-A-001]
- **priority**: P1
- **estimated_complexity**: M

## Scope
Implement `/settings` route with four tabs: API Configuration (model_config visual editor), Preferences Management (global_rules_md / user_preferences_md editing), Brand Kit Configuration (brand_kit editing saved via `PUT /api/settings/brand-kit` to SQLite, no file writes), and Version History (last 20 snapshots with rollback). All APIs are defined in SPEC-A SPEC-0A.4 / SPEC-1A.

## Allowed Files
- `src/frontend/pages/SettingsPage.tsx`
- `src/frontend/components/settings/ApiConfigTab.tsx`
- `src/frontend/components/settings/PreferencesTab.tsx`
- `src/frontend/components/settings/BrandKitTab.tsx`
- `src/frontend/components/settings/VersionHistoryTab.tsx`
- `src/frontend/hooks/useSettings.ts`
- `tests/unit/frontend/SettingsPage.test.tsx`
- `tests/unit/frontend/settings/ApiConfigTab.test.tsx`
- `tests/unit/frontend/settings/PreferencesTab.test.tsx`
- `tests/unit/frontend/settings/BrandKitTab.test.tsx`
- `tests/unit/frontend/settings/VersionHistoryTab.test.tsx`

## Forbidden Files
- `src/backend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: `/settings` route renders page with 4 tabs: API Config, Preferences, Brand Kit, Version History
- [ ] AC-2: API Config tab reads from `GET /api/settings` and writes via `PUT /api/settings/model-config`
- [ ] AC-3: Preferences tab reads from `GET /api/settings/preferences` and writes via `PUT /api/settings/preferences`
- [ ] AC-4: Brand Kit tab saves via `PUT /api/settings/brand-kit` (SQLite, no file write)
- [ ] AC-5: Version History tab loads last 20 snapshots from `GET /api/settings/preferences/snapshots`
- [ ] AC-6: Clicking rollback on a snapshot calls `POST /api/settings/preferences/snapshots/{id}/rollback`
- [ ] AC-7: Rollback operation itself generates a new version record (visible in the list after refresh)

## Verification Commands
```bash
pytest tests/unit/frontend/test_spec_e_004.py -v
tsc --noEmit
```

## Completion Definition
Settings page with 4 functional tabs, all reading/writing through correct API endpoints. Version history shows snapshots and supports rollback. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/frontend/test_spec_e_004.py | test_renders_four_tabs |
| AC-2 | tests/unit/frontend/test_spec_e_004.py | test_loads_and_saves_model_config |
| AC-3 | tests/unit/frontend/test_spec_e_004.py | test_loads_and_saves_preferences |
| AC-4 | tests/unit/frontend/test_spec_e_004.py | test_saves_brand_kit_via_api |
| AC-5 | tests/unit/frontend/test_spec_e_004.py | test_loads_20_snapshots |
| AC-6 | tests/unit/frontend/test_spec_e_004.py | test_rollback_calls_api |
| AC-7 | tests/unit/frontend/test_spec_e_004.py | test_rollback_creates_new_version |
