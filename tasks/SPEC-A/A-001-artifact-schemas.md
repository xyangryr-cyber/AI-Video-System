# [SPEC-A-001] Artifact JSON Schemas (requirements, timeline, style_lock)

## Metadata
- **task_id**: SPEC-A-001
- **spec_ref**: SPEC-0A.1
- **depends_on**: []
- **priority**: P0
- **estimated_complexity**: M

## Scope
Define JSON Schema validation files and corresponding Pydantic models + TypeScript types for the three core artifacts with explicit schemas: `requirements.json`, `timeline.json`, `style_lock.json`. Also define the artifact registry table mapping artifact names to their producer/consumer/validation info.

## Allowed Files
- `src/shared/schemas/artifacts.py`
- `src/shared/types/artifacts.ts`
- `src/shared/schemas/artifact_registry.py`
- `schemas/requirements.schema.json`
- `schemas/timeline.schema.json`
- `schemas/style_lock.schema.json`
- `tests/unit/contracts/test_artifact_schemas.py`

## Forbidden Files
- `src/backend/api/**`
- `src/backend/engine/**`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1: `requirements.json` JSON Schema validates all required fields (project_id, title, topic≥5chars, duration_class enum, target_duration, target_word_count, platform, category, narrative_template enum, voice_preferences, subtitle_preferences)
- [ ] AC-2: `timeline.json` JSON Schema validates segments array (segment_id, text, start_sec, end_sec, audio_path, voice_params, word_count) plus top-level total_duration_sec and sample_rate
- [ ] AC-3: `style_lock.json` JSON Schema validates project_id, locked_at ISO8601, locked_by enum, color_palette, font_family, chart_style
- [ ] AC-4: Pydantic models for all three artifacts pass round-trip serialization tests
- [ ] AC-5: TypeScript interfaces match Pydantic models field-for-field
- [ ] AC-6: Artifact registry maps each of the 8 artifact names to producer, consumer, and validation method

## Verification Commands
```bash
pytest tests/unit/contracts/test_spec_a_001.py -v
mypy src/shared/schemas/artifacts.py --strict
npx tsc --noEmit src/shared/types/artifacts.ts
```

## Completion Definition
All three JSON Schema files exist and validate correct/incorrect payloads. Pydantic models and TS types are defined. Artifact registry covers all 8 artifacts from SPEC-0A.1 table. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/contracts/test_spec_a_001.py | test_requirements_json_schema_valid |
| AC-1 | tests/unit/contracts/test_spec_a_001.py | test_requirements_json_schema_rejects_short_topic |
| AC-2 | tests/unit/contracts/test_spec_a_001.py | test_timeline_json_schema_valid |
| AC-2 | tests/unit/contracts/test_spec_a_001.py | test_timeline_json_schema_rejects_missing_segments |
| AC-3 | tests/unit/contracts/test_spec_a_001.py | test_style_lock_json_schema_valid |
| AC-3 | tests/unit/contracts/test_spec_a_001.py | test_style_lock_json_schema_rejects_invalid_locked_by |
| AC-4 | tests/unit/contracts/test_spec_a_001.py | test_pydantic_round_trip_requirements |
| AC-4 | tests/unit/contracts/test_spec_a_001.py | test_pydantic_round_trip_timeline |
| AC-4 | tests/unit/contracts/test_spec_a_001.py | test_pydantic_round_trip_style_lock |
| AC-5 | tests/unit/contracts/test_spec_a_001.py | test_ts_interfaces_match_pydantic |
| AC-6 | tests/unit/contracts/test_spec_a_001.py | test_artifact_registry_covers_all_8 |
