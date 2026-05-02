# [SPEC-F-009] TTS Provider Abstraction & Voice Preview

## Metadata
- **task_id**: SPEC-F-009
- **spec_ref**: SPEC-19.3
- **depends_on**: [SPEC-A-001, SPEC-F-008]
- **priority**: P1
- **estimated_complexity**: M

## Scope
Implement `TTSProvider` abstraction: `synthesize(text, ssml_tags, voice_params) → AudioResult`. Unsupported parameters must degrade gracefully with `capability_gap` logged (no error thrown). P4 phase generates 2-3 voice preview clips of 15 seconds each. Switching TTS vendor must not require upstream code changes.

## Allowed Files
- `src/frontend/audio/TTSProvider.ts`
- `src/frontend/audio/providers/BaseTTSProvider.ts`
- `src/frontend/audio/providers/AzureTTSProvider.ts`
- `src/frontend/audio/voicePreview.ts`
- `tests/unit/media-render/test_tts_provider.test.ts`

## Forbidden Files
- `src/backend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: Switching TTS vendor (e.g., Azure → another) requires no upstream code changes
- [ ] AC-2: Unsupported parameter triggers log containing `capability_gap`, synthesis does not throw
- [ ] AC-3: Preview files are 14-16 seconds in duration
- [ ] AC-4: `TTSProvider.synthesize()` accepts `text`, `ssml_tags`, `voice_params` and returns `AudioResult`

## Verification Commands
```bash
pytest tests/unit/media-render/test_spec_f_009.py -v
npx tsc --noEmit
```

## Completion Definition
TTSProvider abstraction works with at least one concrete provider, gracefully degrades on unsupported params, generates preview clips in correct duration range, and all tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/media-render/test_spec_f_009.py | test_vendor_switch_no_upstream_change |
| AC-2 | tests/unit/media-render/test_spec_f_009.py | test_unsupported_param_capability_gap_log |
| AC-3 | tests/unit/media-render/test_spec_f_009.py | test_preview_duration_14_to_16s |
| AC-4 | tests/unit/media-render/test_spec_f_009.py | test_synthesize_interface |
