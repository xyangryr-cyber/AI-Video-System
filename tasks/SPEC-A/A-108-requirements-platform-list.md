# [SPEC-A-108] Requirements.platform list[PlatformEntry] (v3.18 D6)

## Metadata
- **task_id**: SPEC-A-108
- **spec_ref**: docs/SPEC_REVISION_REQ_v3.18_PROTOTYPE_DELTA.md D6
- **depends_on**: [SPEC-A-001, SPEC-A-105]
- **priority**: P1
- **estimated_complexity**: M
- **breaking_change**: yes (existing `platform: str` callers must migrate)

## Scope
Refactor `Requirements.platform` from `str` to `list[PlatformEntry]` where `PlatformEntry = {platform: str, role: Literal["primary","secondary"]}`. Real business need: financial videos publish to multiple platforms with different specs (Bilibili primary, Douyin secondary).

## Migration
- `tests/unit/contracts/test_artifact_schemas.py:35` currently has `"platform": "youtube"` — change to `[{"platform": "youtube", "role": "primary"}]`.
- No backend (`src/backend/`) callers exist yet.

## Acceptance Criteria
- [ ] AC-1: PlatformEntry Pydantic model exists with `platform: str` (min 1) and `role: Literal["primary","secondary"]`.
- [ ] AC-2: Requirements.platform field type is `List[PlatformEntry]` with `min_length=1`.
- [ ] AC-3: TS mirrors as `interface PlatformEntry { platform: string; role: "primary" | "secondary"; }` and `Requirements.platform: PlatformEntry[]`.
- [ ] AC-4: Fixture has Bilibili primary + Douyin secondary entries.
- [ ] AC-5: All existing artifact-schema tests still pass after migration.

## Verification Commands
```bash
.venv/bin/python -m pytest tests/unit/contracts/test_spec_a_108.py -v
.venv/bin/python -m pytest tests/unit/contracts/test_artifact_schemas.py -v
```

## Test Mapping
| AC | Test Function | File |
|----|--------------|------|
| AC-1 | test_platformentry_role_constrained_to_primary_secondary | tests/unit/contracts/test_spec_a_108.py |
| AC-2 | test_requirements_platform_must_be_list_of_platformentry | tests/unit/contracts/test_spec_a_108.py |
| AC-4 | test_requirements_platform_rejects_string | tests/unit/contracts/test_spec_a_108.py |
| AC-4 | test_requirements_platform_requires_at_least_one_entry | tests/unit/contracts/test_spec_a_108.py |
