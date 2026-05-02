# [SPEC-F-008] Voice Parameter System & SSML Builder

## Metadata
- **task_id**: SPEC-F-008
- **spec_ref**: SPEC-19.1, SPEC-19.2
- **depends_on**: [SPEC-A-001]
- **priority**: P1
- **estimated_complexity**: M

## Scope
Implement voice_direction → segment_voice_overrides lookup conversion (pure function, zero LLM calls), SSML builder for key_emphasis → `<emphasis>`, pause_after → `<break>`, cross-segment emotion transition → 800ms break, and numeric-dense sentence detection → `<prosody rate="slow">` wrapping. Priority: segment_voice_overrides > numeric-aware slowdown > global rate_wpm.

## Allowed Files
- `src/frontend/audio/voiceParamConverter.ts`
- `src/frontend/audio/ssmlBuilder.ts`
- `tests/unit/media-render/test_voice_params.test.ts`

## Forbidden Files
- `src/backend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: `style_degree` validates range [0.01, 2.0], rejects out-of-range
- [ ] AC-2: Same `voice_direction` input produces identical output on two calls (pure function)
- [ ] AC-3: Conversion code has zero LLM API calls
- [ ] AC-4: `pace=much_slower` → `rate_multiplier=0.8`; all 5 pace levels match lookup table
- [ ] AC-5: `energy=high` → volume +10%; all 3 energy levels match lookup table
- [ ] AC-6: Adjacent segments `sad→excited` → 800ms `<break>` inserted between them
- [ ] AC-7: Numeric-dense sentence wrapped in `<prosody rate="slow">`
- [ ] AC-8: `ssml_builder` module has zero LLM calls

## Verification Commands
```bash
pytest tests/unit/media-render/test_spec_f_008.py -v
npx tsc --noEmit
```

## Completion Definition
Voice parameter converter and SSML builder are pure deterministic functions, correctly map all direction values per spec lookup tables, handle emotion transitions and numeric slowdown, with all tests passing.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/media-render/test_spec_f_008.py | test_style_degree_range_validation |
| AC-2 | tests/unit/media-render/test_spec_f_008.py | test_voice_direction_deterministic |
| AC-3 | tests/unit/media-render/test_spec_f_008.py | test_no_llm_calls_in_converter |
| AC-4 | tests/unit/media-render/test_spec_f_008.py | test_pace_lookup_table |
| AC-5 | tests/unit/media-render/test_spec_f_008.py | test_energy_lookup_table |
| AC-6 | tests/unit/media-render/test_spec_f_008.py | test_emotion_transition_break |
| AC-7 | tests/unit/media-render/test_spec_f_008.py | test_numeric_dense_prosody_slow |
| AC-8 | tests/unit/media-render/test_spec_f_008.py | test_no_llm_calls_in_ssml_builder |
