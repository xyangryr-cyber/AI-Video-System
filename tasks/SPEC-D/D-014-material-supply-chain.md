# [SPEC-D-014] Material Supply Chain Resilience (SPEC-26)

## Metadata
- **task_id**: SPEC-D-014
- **spec_ref**: SPEC-26.1, SPEC-26.2
- **depends_on**: [SPEC-D-005, SPEC-D-007]
- **priority**: P1
- **estimated_complexity**: M

## Scope
Implement the material supply chain resilience layer covering SFX/BGM multi-level fallback (SPEC-26.1) and B-Roll 3-level fallback with offline mode (SPEC-26.2). This task builds the shared fallback infrastructure that BGMAgent, SFXAgent, and BRollAgent use. Includes: source provider abstraction, fallback chain execution with timing constraints, degradation logging (source_attempted/reason_failed/source_used), quality filtering pipeline, and offline mode banner for complete API unavailability.

## Allowed Files
- `src/backend/services/material_fallback.py`
- `src/backend/services/material_providers/sfx_provider.py`
- `src/backend/services/material_providers/bgm_provider.py`
- `src/backend/services/material_providers/broll_provider.py`
- `src/backend/services/material_providers/base_material_provider.py`
- `src/backend/services/quality_filter.py`
- `tests/unit/services/test_material_fallback.py`
- `tests/unit/services/test_quality_filter.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**`
- `src/shared/schemas/**`

## Acceptance Criteria
- [ ] AC-1: SFX 3-level fallback: built-in library (sfx_index.json >= 50 entries) -> Freesound CC0 -> user upload
- [ ] AC-2: Freesound results filtered to license=CC0 only
- [ ] AC-3: BGM 2-level fallback: Mubert API -> local library (>= 10 tracks); Mubert unavailable -> degrade to local within 2s
- [ ] AC-4: B-Roll 3-level fallback: Pexels SDK -> Pixabay SDK -> Placeholder (Pillow + description text, is_placeholder=true); Pexels fail -> Pixabay within 3s
- [ ] AC-5: Quality filter pipeline: resolution >= 720p, watermark detection (edge region transparency analysis), aspect ratio 16:9 matching; sub-threshold materials filtered out
- [ ] AC-6: Placeholder contains description text and is_placeholder=true marker
- [ ] AC-7: All API unavailable -> offline mode banner; offline mode still completes full video generation (with placeholders/local materials)
- [ ] AC-8: Degradation log for every fallback: source_attempted, reason_failed, source_used (structured JSON log)

## Verification Commands
```bash
pytest tests/unit/pipeline/test_spec_d_014.py -v
mypy src/backend/services/material_fallback.py --strict
```

## Completion Definition
Material fallback chains for SFX (3-level), BGM (2-level), and B-Roll (3-level) implemented with timing constraints. Quality filter pipeline works for resolution/watermark/aspect. Offline mode produces complete videos with degraded materials. Fallback logging is structured. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/pipeline/test_spec_d_014.py | test_sfx_builtin_index_50_entries |
| AC-1 | tests/unit/pipeline/test_spec_d_014.py | test_sfx_fallback_to_freesound |
| AC-1 | tests/unit/pipeline/test_spec_d_014.py | test_sfx_fallback_to_user_upload |
| AC-2 | tests/unit/pipeline/test_spec_d_014.py | test_freesound_cc0_only |
| AC-3 | tests/unit/pipeline/test_spec_d_014.py | test_bgm_mubert_to_local_within_2s |
| AC-4 | tests/unit/pipeline/test_spec_d_014.py | test_broll_pexels_to_pixabay_within_3s |
| AC-4 | tests/unit/pipeline/test_spec_d_014.py | test_broll_fallback_to_placeholder |
| AC-5 | tests/unit/pipeline/test_spec_d_014.py | test_resolution_below_720p_filtered |
| AC-5 | tests/unit/pipeline/test_spec_d_014.py | test_watermark_detected_filtered |
| AC-5 | tests/unit/pipeline/test_spec_d_014.py | test_aspect_ratio_mismatch_filtered |
| AC-6 | tests/unit/pipeline/test_spec_d_014.py | test_placeholder_has_description_and_flag |
| AC-7 | tests/unit/pipeline/test_spec_d_014.py | test_offline_mode_banner |
| AC-7 | tests/unit/pipeline/test_spec_d_014.py | test_offline_mode_completes_video |
| AC-8 | tests/unit/pipeline/test_spec_d_014.py | test_degradation_log_structured |
