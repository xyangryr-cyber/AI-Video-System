# [SPEC-A-003] Settings, Preferences & BrandKit Contracts

## Metadata
- **task_id**: SPEC-A-003
- **spec_ref**: SPEC-0A.4, SPEC-0A.5
- **depends_on**: [SPEC-A-001]
- **priority**: P1
- **estimated_complexity**: M

## Scope
Define contracts for Settings/Preferences/Snapshot API payloads and the BrandKit schema. Includes the preference write flow (auto-snapshot before update) and rollback flow (rollback also creates snapshot + writes event) as documented state machines. Establish that SQLite is the runtime authority for brand_kit, not the filesystem.

## Allowed Files
- `src/shared/types/settings.ts`
- `src/shared/schemas/settings.py`
- `src/shared/schemas/brand_kit.py`
- `src/shared/types/brand_kit.ts`
- `tests/unit/contracts/test_settings_brandkit.py`

## Forbidden Files
- `src/backend/api/**`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1: `BrandKit` Pydantic model validates logo (path, position enum, opacity 0-1), watermark, intro/outro_template, color_palette, font_family
- [ ] AC-2: `BrandKit` TS interface matches Pydantic model
- [ ] AC-3: Settings response schema includes model_config and brand_kit sections
- [ ] AC-4: Preferences response schema includes global_rules_md and user_preferences_md
- [ ] AC-5: Preferences update request schema supports optional global_rules_md and user_preferences_md
- [ ] AC-6: Snapshot list response schema includes array of {id, created_at, preview}
- [ ] AC-7: Preference write flow documented: snapshot-first-then-update, returns snapshot_id
- [ ] AC-8: Rollback flow documented: snapshot-current, overwrite from target, write preference.rollback event, return new snapshot_id

## Verification Commands
```bash
pytest tests/unit/contracts/test_settings_brandkit.py -v
mypy src/shared/schemas/settings.py --strict
mypy src/shared/schemas/brand_kit.py --strict
npx tsc --noEmit src/shared/types/settings.ts src/shared/types/brand_kit.ts
```

## Completion Definition
All Settings/Preferences/Snapshot/BrandKit types defined in both TS and Python. Write and rollback flows encoded as documented constants or flow descriptions in code. Tests validate schema and flow invariants.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/contracts/test_settings_brandkit.py | test_brand_kit_valid |
| AC-1 | tests/unit/contracts/test_settings_brandkit.py | test_brand_kit_rejects_invalid_position |
| AC-2 | tests/unit/contracts/test_settings_brandkit.py | test_brand_kit_ts_matches_pydantic |
| AC-3 | tests/unit/contracts/test_settings_brandkit.py | test_settings_response_schema |
| AC-4 | tests/unit/contracts/test_settings_brandkit.py | test_preferences_response_schema |
| AC-5 | tests/unit/contracts/test_settings_brandkit.py | test_preferences_update_optional_fields |
| AC-6 | tests/unit/contracts/test_settings_brandkit.py | test_snapshot_list_response |
| AC-7 | tests/unit/contracts/test_settings_brandkit.py | test_preference_write_flow_invariants |
| AC-8 | tests/unit/contracts/test_settings_brandkit.py | test_preference_rollback_flow_invariants |
